import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import db  # noqa: E402
from app.advice import Context, build_advice, infer_scenario, lot, money, pct, round_price  # noqa: E402
from app.repository import (  # noqa: E402
    create_daily_analysis,
    create_kline,
    create_news,
    create_position,
    create_volume,
    dashboard_summary,
    deepseek_status,
    delete_position,
    latest_context,
    list_analysis_reports,
    list_advice,
    list_kline,
    list_news,
    list_positions,
    list_volume,
    rebuild_advice,
    seed_if_empty,
    update_position,
)
from app.server import ApiError, Handler, build_advice_csv, build_realtime_kline_payload, json_bytes  # noqa: E402


class TempDatabaseMixin:
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_data_dir = db.DATA_DIR
        db.DATA_DIR = Path(self.tempdir.name)
        db.DB_PATH = db.DATA_DIR / "test_stock_discipline.db"
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        db.DATA_DIR = self.original_data_dir
        self.tempdir.cleanup()


class AdviceEngineTests(unittest.TestCase):
    def test_money_percent_rounding_and_lots(self):
        self.assertEqual(money(120.333), "120.3元")
        self.assertEqual(money(18.456), "18.46元")
        self.assertEqual(pct(-0.1532), "-15.3%")
        self.assertEqual(pct(0.021), "+2.1%")
        self.assertEqual(round_price(47.26), 47.3)
        self.assertEqual(round_price(57.26), 57.5)
        self.assertEqual(lot(1200, 0.25), 300)
        self.assertEqual(lot(50, 0.5), 50)

    def test_weak_following_position_blocks_add_and_forces_exit_plan(self):
        position = {
            "id": 1,
            "name": "弱势样例",
            "quantity": 200,
            "cost_price": 22.61,
            "current_price": 18.8,
            "category": "弱势跟风",
        }
        advice = build_advice(position)
        self.assertEqual(advice["risk_level"], "高")
        self.assertEqual(advice["discipline_passed"], 0)
        self.assertIn("全程禁止加仓", advice["add_reference"])
        self.assertIn("直接全部止损", advice["stop_trigger"])
        self.assertIn("弱势票优先退出", advice["action_advice"])

    def test_core_deep_loss_blocks_position_expansion(self):
        position = {
            "id": 2,
            "name": "核心样例",
            "quantity": 500,
            "cost_price": 69.43,
            "current_price": 57.5,
            "category": "核心赛道",
        }
        advice = build_advice(position)
        self.assertEqual(advice["risk_level"], "高")
        self.assertEqual(advice["discipline_passed"], 1)
        self.assertIn("浮亏较深", advice["action_advice"])
        self.assertIn("当前禁止加仓", advice["add_reference"])

    def test_news_and_volume_can_mark_distribution_risk(self):
        ctx = Context(
            latest_news={"scenario": "主力出货风险", "sentiment": "利好兑现"},
            latest_volume={"volume_state": "放量滞涨", "volume_ratio": 2.1, "sell_risk_score": 82},
        )
        self.assertEqual(infer_scenario("核心赛道", -0.05, ctx), "主力出货风险")
        advice = build_advice(
            {
                "id": 3,
                "name": "风险样例",
                "quantity": 1000,
                "cost_price": 10,
                "current_price": 11,
                "category": "核心赛道",
            },
            ctx,
        )
        self.assertEqual(advice["risk_level"], "高")
        self.assertEqual(advice["discipline_passed"], 0)
        self.assertIn("禁止加仓", advice["add_reference"])

    def test_regulatory_or_hard_negative_news_forces_high_risk_exit(self):
        ctx = Context(
            latest_news={"scenario": "", "sentiment": "监管风险"},
            latest_volume={"volume_state": "温和放量", "volume_ratio": 1.3, "sell_risk_score": 40},
        )
        advice = build_advice(
            {
                "id": 4,
                "name": "监管样例",
                "quantity": 300,
                "cost_price": 30,
                "current_price": 29,
                "category": "核心赛道",
            },
            ctx,
        )
        self.assertEqual(advice["scenario"], "高风险退出")
        self.assertEqual(advice["discipline_passed"], 0)
        self.assertIn("硬风险未解除前禁止加仓", advice["add_reference"])


class RepositoryTests(TempDatabaseMixin, unittest.TestCase):
    def test_schema_seed_and_summary(self):
        seed_if_empty()
        positions = list_positions()
        self.assertEqual(len(positions), 5)
        advice = rebuild_advice()
        self.assertEqual(len(advice), 5)
        summary = dashboard_summary()
        self.assertEqual(summary["position_count"], 5)
        self.assertLess(summary["total_pnl"], 0)
        self.assertGreaterEqual(summary["discipline_blocked_count"], 2)

    def test_create_update_delete_position(self):
        created = create_position(
            {
                "name": "测试股票",
                "quantity": 300,
                "cost_price": 10.5,
                "current_price": 9.8,
                "category": "观察仓",
                "sector": "测试",
            }
        )
        self.assertEqual(created["name"], "测试股票")
        updated = update_position(created["id"], {"current_price": 10.8, "category": "核心赛道"})
        self.assertEqual(updated["current_price"], 10.8)
        self.assertEqual(updated["category"], "核心赛道")
        delete_position(created["id"])
        self.assertEqual(list_positions(), [])

    def test_news_and_volume_are_linked_to_latest_advice_context(self):
        position = create_position(
            {
                "name": "联动股票",
                "quantity": 1000,
                "cost_price": 10,
                "current_price": 10.5,
                "category": "核心赛道",
            }
        )
        create_news(
            {
                "name": "联动股票",
                "title": "利好兑现后高位放量",
                "source": "测试源",
                "sentiment": "利好兑现",
                "importance": 88,
                "scenario": "主力出货风险",
            }
        )
        create_volume(
            {
                "name": "联动股票",
                "volume_state": "放量滞涨",
                "volume_ratio": 2.3,
                "sell_risk_score": 86,
            }
        )
        ctx = latest_context(position)
        self.assertEqual(ctx.latest_news["scenario"], "主力出货风险")
        self.assertEqual(ctx.latest_volume["volume_state"], "放量滞涨")
        advice = rebuild_advice()[0]
        self.assertEqual(advice["scenario"], "主力出货风险")
        self.assertEqual(advice["discipline_passed"], 0)
        self.assertEqual(len(list_news()), 1)
        self.assertEqual(len(list_volume()), 1)

    def test_list_advice_auto_rebuilds_when_missing(self):
        create_position(
            {
                "name": "自动建议",
                "quantity": 100,
                "cost_price": 20,
                "current_price": 19,
                "category": "观察仓",
            }
        )
        advice = list_advice()
        self.assertEqual(len(advice), 1)
        self.assertIn("trim_trigger", advice[0])

    def test_kline_seed_and_manual_upsert(self):
        seed_if_empty()
        bars = list_kline(name="中天科技", limit=20)
        self.assertGreaterEqual(len(bars), 20)
        self.assertIn("open_price", bars[0])
        saved = create_kline(
            {
                "name": "测试股票",
                "trade_date": "2026-07-06",
                "open_price": 10,
                "high_price": 11,
                "low_price": 9.5,
                "close_price": 10.8,
                "volume": 100000,
                "amount": 1080000,
            }
        )
        self.assertEqual(saved["close_price"], 10.8)
        self.assertEqual(len(list_kline(name="测试股票")), 1)

    def test_realtime_kline_falls_back_to_local_cache_when_source_empty(self):
        seed_if_empty()
        payload = build_realtime_kline_payload(
            name="中天科技",
            days=5,
            fetcher=lambda symbol, name, days: [],
        )
        self.assertEqual(payload["source"], "local_cache")
        self.assertEqual(payload["symbol"], "sh.600522")
        self.assertEqual(len(payload["bars"]), 5)

    def test_realtime_kline_saves_remote_bars(self):
        payload = build_realtime_kline_payload(
            name="中天科技",
            symbol="sh.600522",
            days=1,
            fetcher=lambda symbol, name, days: [
                {
                    "symbol": symbol,
                    "name": name,
                    "trade_date": "2026-07-06",
                    "open_price": 50,
                    "high_price": 52,
                    "low_price": 49,
                    "close_price": 51,
                    "volume": 1000000,
                    "amount": 51000000,
                    "turnover_rate": 2.5,
                }
            ],
        )
        self.assertEqual(payload["source"], "baostock")
        self.assertEqual(payload["saved"], 1)
        bars = list_kline(name="中天科技", symbol="sh.600522", limit=5)
        self.assertEqual(bars[-1]["close_price"], 51)

    def test_daily_analysis_falls_back_when_deepseek_key_missing(self):
        seed_if_empty()
        rebuild_advice()
        report = create_daily_analysis({"extra_note": "测试日报"})
        self.assertIn(report["provider"], {"local", "deepseek"})
        self.assertTrue(report["content"])
        reports = list_analysis_reports()
        self.assertEqual(len(reports), 1)
        status = deepseek_status()
        self.assertIn("configured", status)


class ExportAndSurfaceTests(TempDatabaseMixin, unittest.TestCase):
    def test_advice_csv_contains_attachment_style_columns_and_rows(self):
        seed_if_empty()
        rebuild_advice()
        body = build_advice_csv(list_advice())
        text = body.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        self.assertEqual(rows[0][0], "标的")
        self.assertIn("减仓触发价（分批执行）", rows[0])
        self.assertIn("止损触发价（跌破刚性执行）", rows[0])
        self.assertIn("加仓参考价（仅企稳后）", rows[0])
        self.assertEqual(len(rows), 6)
        self.assertTrue(any(row[0] == "中天科技" for row in rows[1:]))

    def test_json_bytes_preserves_chinese(self):
        body = json_bytes({"标的": "中天科技"})
        self.assertIn("中天科技".encode("utf-8"), body)

    def test_handler_path_id_validation(self):
        handler = object.__new__(Handler)
        self.assertEqual(handler._path_id("/api/positions/12", "/api/positions/"), 12)
        with self.assertRaises(ApiError):
            handler._path_id("/api/positions/abc", "/api/positions/")

    def test_frontend_has_required_workflows(self):
        package = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
        root_files = {path.name for path in (ROOT / "frontend").iterdir() if path.is_file()}
        app = (ROOT / "frontend" / "src" / "App.vue").read_text(encoding="utf-8")
        kline = (ROOT / "frontend" / "src" / "components" / "KlineChart.vue").read_text(encoding="utf-8")
        kline_page = (ROOT / "frontend" / "src" / "pages" / "KlineVolume.vue").read_text(encoding="utf-8")
        server = (ROOT / "backend" / "app" / "server.py").read_text(encoding="utf-8")
        holdings = (ROOT / "frontend" / "src" / "pages" / "Holdings.vue").read_text(encoding="utf-8")
        news = (ROOT / "frontend" / "src" / "pages" / "NewsCenter.vue").read_text(encoding="utf-8")
        analysis = (ROOT / "frontend" / "src" / "pages" / "AiAnalysis.vue").read_text(encoding="utf-8")

        self.assertIn("index.html", root_files)
        self.assertNotIn("holdings.html", root_files)
        self.assertNotIn("news.html", root_files)
        self.assertNotIn("analysis.html", root_files)
        self.assertNotIn("styles.css", root_files)
        self.assertIn("vue", package["dependencies"])
        self.assertIn("element-plus", package["dependencies"])
        self.assertIn("klinecharts", package["dependencies"])
        self.assertNotIn("lightweight-charts", package["dependencies"])
        self.assertNotIn("echarts", package["dependencies"])
        self.assertIn("持仓建议", app)
        self.assertIn("K线量能", app)
        self.assertIn("klinecharts", kline)
        self.assertIn("applyNewData", kline)
        self.assertIn('props.mode === "daily" ? [5, 10, 20, 30, 60] : [5, 10, 20]', kline)
        self.assertIn("mousemove", kline)
        self.assertIn("rawVolume / 100", kline)
        self.assertIn("trade-tooltip", kline)
        self.assertIn("LineType.Solid", kline)
        self.assertIn("setMaxOffsetRightDistance(0)", kline)
        self.assertIn("OnVisibleRangeChange", kline)
        self.assertIn("requestMoreHistory", kline)
        self.assertIn("分时K线", kline_page)
        self.assertIn("/api/kline/intraday", kline_page)
        self.assertIn("dailyDays.value + 180", kline_page)
        self.assertIn("setInterval", kline_page)
        self.assertIn("/api/kline/intraday", server)
        self.assertIn("/api/advice/rebuild", holdings)
        self.assertIn("/api/news", news)
        self.assertIn("/api/analysis/daily", analysis)


if __name__ == "__main__":
    unittest.main(verbosity=2)

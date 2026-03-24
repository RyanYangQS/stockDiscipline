/**
 * 本地静态文件服务器
 * 用于托管股票交易纪律系统演示页面
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 3000;
const ROOT_DIR = __dirname;

// MIME类型映射
const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
    // 解析URL
    const parsedUrl = url.parse(req.url, true);
    let pathname = parsedUrl.pathname;

    // 默认访问 index.html
    if (pathname === '/') {
        pathname = '/index.html';
    }

    // 安全检查：防止路径遍历攻击
    const safePath = path.normalize(pathname).replace(/^(\.\.[\/\\])+/, '');
    const filePath = path.join(ROOT_DIR, safePath);

    // 获取文件扩展名
    const ext = path.extname(filePath).toLowerCase();
    const contentType = mimeTypes[ext] || 'application/octet-stream';

    // 读取文件
    fs.readFile(filePath, (err, content) => {
        if (err) {
            if (err.code === 'ENOENT') {
                // 文件不存在
                res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
                res.end(`
                    <!DOCTYPE html>
                    <html>
                    <head><title>404 - 文件不存在</title></head>
                    <body style="font-family: Arial; background: #1a1a2e; color: #e0e0e0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
                        <div style="text-align: center;">
                            <h1 style="font-size: 48px; margin-bottom: 20px;">404</h1>
                            <p>文件不存在: ${pathname}</p>
                            <a href="/" style="color: #667eea;">返回首页</a>
                        </div>
                    </body>
                    </html>
                `);
            } else {
                // 服务器错误
                res.writeHead(500, { 'Content-Type': 'text/plain' });
                res.end('服务器内部错误');
            }
        } else {
            // 成功返回文件
            res.writeHead(200, {
                'Content-Type': contentType,
                'Cache-Control': 'no-cache'
            });
            res.end(content);
        }
    });
});

server.listen(PORT, () => {
    console.log(`
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   📈 个人股票交易纪律系统 - 本地服务已启动                 ║
║                                                          ║
║   访问地址: http://localhost:${PORT}                        ║
║                                                          ║
║   按 Ctrl+C 停止服务                                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    `);
});

server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`端口 ${PORT} 已被占用，请先关闭占用该端口的程序，或修改 PORT 变量`);
    } else {
        console.error('服务器错误:', err);
    }
    process.exit(1);
});

export async function apiGet(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function apiPost(path, body = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function apiPut(path, body = {}) {
  const response = await fetch(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function apiDelete(path) {
  const response = await fetch(path, { method: "DELETE" });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

async function readError(response) {
  try {
    const data = await response.json();
    return data.error || response.statusText;
  } catch {
    return response.statusText;
  }
}


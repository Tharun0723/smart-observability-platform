export default async function handler(req, res) {
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    return res.status(405).json({ detail: "Method not allowed" });
  }

  const backend = (process.env.BACKEND_URL || "").replace(/\/+$/, "");
  const key = process.env.ADMIN_API_KEY;
  const path = req.query.path;

  if (!backend || !key || !path) {
    return res.status(500).json({ detail: "Proxy configuration missing" });
  }

  try {
    const apiPath = Array.isArray(path) ? path.join("/") : String(path);
    const query = new URLSearchParams();

    for (const [name, value] of Object.entries(req.query)) {
      if (name === "path") continue;
      for (const item of Array.isArray(value) ? value : [value]) {
        query.append(name, String(item));
      }
    }

    const url = `${backend}/${apiPath.replace(/^\/+/, "")}${query.size ? `?${query}` : ""}`;

    const upstream = await fetch(url, {
      headers: {
        "X-Admin-API-Key": key,
        Accept: "application/json",
      },
      cache: "no-store",
    });

    res.statusCode = upstream.status;
    res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/json");
    res.setHeader("Cache-Control", "no-store");
    return res.end(Buffer.from(await upstream.arrayBuffer()));
  } catch (error) {
    console.error("NEXORA proxy error:", error);
    return res.status(502).json({ detail: "Cannot reach NEXORA backend" });
  }
}

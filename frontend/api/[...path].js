export default async function handler(req, res) {
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    return res.status(405).json({ detail: "Method not allowed" });
  }

  const backendUrl = (process.env.BACKEND_URL || "").replace(/\/+$/, "");
  const adminKey = process.env.ADMIN_API_KEY;

  if (!backendUrl || !adminKey) {
    return res.status(500).json({
      detail: "Backend configuration missing",
    });
  }

  try {
    const incoming = new URL(req.url, "https://vercel.invalid");
    const target = new URL(
      incoming.pathname + incoming.search,
      backendUrl
    );

    const upstream = await fetch(target, {
      method: "GET",
      headers: {
        "X-Admin-API-Key": adminKey,
        Accept: "application/json",
      },
      cache: "no-store",
    });

    res.statusCode = upstream.status;
    res.setHeader(
      "Content-Type",
      upstream.headers.get("content-type") || "application/json"
    );
    res.setHeader("Cache-Control", "no-store");

    return res.end(Buffer.from(await upstream.arrayBuffer()));
  } catch {
    return res.status(502).json({
      detail: "Unable to reach NEXORA backend",
    });
  }
}
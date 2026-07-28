export interface TelegramConfig {
  botToken: string;
  chatId: string;
}

export async function sendToTelegram(
  cfg: TelegramConfig,
  text: string,
  photo?: Buffer
): Promise<void> {
  const base = `https://api.telegram.org/bot${cfg.botToken}`;

  let res: Response;
  if (photo) {
    const form = new FormData();
    form.set("chat_id", cfg.chatId);
    form.set("caption", text);
    form.set("photo", new Blob([new Uint8Array(photo)], { type: "image/png" }), "altrank-movers.png");
    res = await fetch(`${base}/sendPhoto`, { method: "POST", body: form });
  } else {
    res = await fetch(`${base}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: cfg.chatId, text }),
    });
  }

  if (!res.ok) {
    throw new Error(`Telegram send failed: HTTP ${res.status} ${await res.text()}`);
  }
}

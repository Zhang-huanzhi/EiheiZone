"use client";

import { Bell, Copy, Link2, Unlink } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { createWeChatBindingCode, getWeChatBindingStatus, unbindWeChat } from "@/features/notifications/notification-api";
import type { WeChatBindingStatus } from "@/features/notifications/notification-types";

export function NotificationSettings() {
  const [status, setStatus] = useState<WeChatBindingStatus | null>(null);
  const [code, setCode] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { getWeChatBindingStatus().then(setStatus).catch(() => setError("暂时无法读取微信绑定状态。")); }, []);

  async function generateCode() {
    setBusy(true); setError(null); setMessage(null);
    try { const result = await createWeChatBindingCode(); setCode(result.code); setExpiresAt(result.expires_at); setMessage("请关注测试号后，把绑定码发送给测试号。绑定码 10 分钟内有效。"); }
    catch { setError("暂时无法生成绑定码，请重试。"); }
    finally { setBusy(false); }
  }

  async function copyCode() {
    if (!code) return;
    await navigator.clipboard.writeText(code);
    setMessage("绑定码已复制。");
  }

  async function removeBinding() {
    setBusy(true); setError(null); setMessage(null);
    try { await unbindWeChat(); setStatus({ bound: false, bound_at: null }); setCode(null); setMessage("微信绑定已解除。"); }
    catch { setError("暂时无法解除绑定，请重试。"); }
    finally { setBusy(false); }
  }

  return (
    <section className="max-w-2xl space-y-6">
      <header className="space-y-2"><p className="text-sm font-medium text-muted-foreground">通知</p><h2 className="text-2xl font-semibold">微信通知</h2><p className="text-muted-foreground">绑定后，新的家庭近况、问题和问题回复会提醒你。</p></header>
      <div className="space-y-4 rounded-md border p-5">
        <div className="flex items-start gap-3"><Bell className="mt-0.5 size-5" aria-hidden="true" /><div><h3 className="font-medium">微信测试号</h3><p className="text-sm text-muted-foreground">请先关注测试号，再把网站生成的绑定码发给它。</p></div></div>
        {status?.bound ? <p className="text-sm text-green-700">已绑定微信，可以接收通知。</p> : <p className="text-sm text-muted-foreground">当前尚未绑定微信。</p>}
        {code ? <div className="space-y-2 rounded-md bg-muted p-4"><p className="text-sm">绑定码</p><p className="font-mono text-2xl tracking-widest">{code}</p><p className="text-xs text-muted-foreground">有效期至 {expiresAt ? new Date(expiresAt).toLocaleString("zh-CN") : "10 分钟内"}</p><Button type="button" variant="outline" onClick={copyCode}><Copy data-icon="inline-start" />复制绑定码</Button></div> : null}
        <div className="flex flex-wrap gap-2"><Button disabled={busy} type="button" onClick={generateCode}><Link2 data-icon="inline-start" />{code ? "重新生成绑定码" : "生成绑定码"}</Button>{status?.bound ? <Button disabled={busy} type="button" variant="outline" onClick={removeBinding}><Unlink data-icon="inline-start" />解除绑定</Button> : null}</div>
        {message ? <p className="text-sm text-muted-foreground" role="status">{message}</p> : null}{error ? <p className="text-sm text-destructive" role="alert">{error}</p> : null}
      </div>
    </section>
  );
}

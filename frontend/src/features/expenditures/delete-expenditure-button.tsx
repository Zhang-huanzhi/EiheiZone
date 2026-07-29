"use client";

import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { deleteExpenditure } from "@/features/expenditures/expenditure-api";
import { formatBusinessDate } from "@/features/expenditures/expenditure-display";
import { formatExactAmount } from "@/features/expenditures/expenditure-money";
import type { ExpenditureRecord } from "@/features/expenditures/expenditure-types";
import { ApiRequestError } from "@/lib/api/client";

export function DeleteExpenditureButton({ expenditure }: { expenditure: ExpenditureRecord }) {
  const router = useRouter();
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleDelete() {
    if (isDeleting) return;
    setIsDeleting(true);
    setErrorMessage(null);
    try {
      await deleteExpenditure(expenditure.id);
      router.replace("/owner/expenditures");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        router.replace(`/login?next=${encodeURIComponent("/owner/expenditures")}`);
        router.refresh();
        return;
      }
      if (error instanceof ApiRequestError && error.status === 403) {
        setErrorMessage("当前账号没有删除权限。");
      } else if (error instanceof ApiRequestError && error.status === 404) {
        setErrorMessage("这条重大支出记录已不存在。");
      } else {
        setErrorMessage("暂时无法删除，请重试。");
      }
      setIsDeleting(false);
    }
  }

  if (!isConfirming) {
    return (
      <Button onClick={() => setIsConfirming(true)} type="button" variant="destructive">
        <Trash2 data-icon="inline-start" />
        删除记录
      </Button>
    );
  }

  return (
    <section aria-labelledby="delete-expenditure-title" className="space-y-3 border border-destructive/30 p-4" role="dialog">
      <div className="space-y-1">
        <h2 className="font-medium" id="delete-expenditure-title">确认删除重大支出？</h2>
        <p className="text-sm text-muted-foreground">
          {formatBusinessDate(expenditure.spent_on)} · {expenditure.category} · {formatExactAmount(expenditure.amount, expenditure.currency)}，删除后无法恢复。
        </p>
      </div>
      {errorMessage ? <p className="text-sm text-destructive" role="alert">{errorMessage}</p> : null}
      <div className="flex flex-wrap gap-2">
        <Button disabled={isDeleting} onClick={() => setIsConfirming(false)} type="button" variant="outline">取消</Button>
        <Button disabled={isDeleting} onClick={handleDelete} type="button" variant="destructive">
          {isDeleting ? "正在删除..." : "确认删除"}
        </Button>
      </div>
    </section>
  );
}

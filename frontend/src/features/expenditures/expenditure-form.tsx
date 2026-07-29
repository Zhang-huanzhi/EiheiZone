"use client";

import { Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  createExpenditure,
  updateExpenditure,
} from "@/features/expenditures/expenditure-api";
import {
  canonicalizeAmount,
  validateAmountInput,
} from "@/features/expenditures/expenditure-money";
import type {
  ExpenditureCreateInput,
  ExpenditureRecord,
  ExpenditureUpdateInput,
} from "@/features/expenditures/expenditure-types";
import { ApiRequestError } from "@/lib/api/client";

type ExpenditureFormProps = {
  initialExpenditure?: ExpenditureRecord;
};

type ExpenditureField = "spent_on" | "amount" | "currency" | "category" | "description";
type FieldErrors = Partial<Record<ExpenditureField, string>>;

const MAX_CATEGORY_LENGTH = 80;
const MAX_DESCRIPTION_LENGTH = 2000;

export function ExpenditureForm({ initialExpenditure }: ExpenditureFormProps) {
  const router = useRouter();
  const [spentOn, setSpentOn] = useState(initialExpenditure?.spent_on ?? "");
  const [amount, setAmount] = useState(initialExpenditure?.amount ?? "");
  const [currency, setCurrency] = useState(initialExpenditure?.currency ?? "CNY");
  const [category, setCategory] = useState(initialExpenditure?.category ?? "");
  const [description, setDescription] = useState(initialExpenditure?.description ?? "");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const errors = validate();
    setFieldErrors(errors);
    setFormError(null);
    if (Object.keys(errors).length > 0) {
      return;
    }

    const input: ExpenditureCreateInput = {
      spent_on: spentOn,
      amount,
      currency: currency.toUpperCase(),
      category: category.trim(),
      description,
    };

    setIsSubmitting(true);
    if (initialExpenditure) {
      const changed = changedFields(initialExpenditure, input);
      if (Object.keys(changed).length === 0) {
        setFormError("没有需要保存的修改。");
        setIsSubmitting(false);
        return;
      }
      await submit(() => updateExpenditure(initialExpenditure.id, changed));
      return;
    }
    await submit(() => createExpenditure(input));
  }

  async function submit(action: () => Promise<unknown>) {
    try {
      await action();
      router.replace("/owner/expenditures");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.status === 401) {
          router.replace(`/login?next=${encodeURIComponent("/owner/expenditures")}`);
          router.refresh();
          return;
        }
        if (error.status === 403) {
          setFormError("当前账号没有管理重大支出的权限。");
        } else if (error.status === 404) {
          setFormError("这条重大支出记录已不存在。");
        } else if (error.status === 422) {
          setFieldErrors(toFieldErrors(error));
          setFormError("请检查标记的字段。");
        } else {
          setFormError("暂时无法保存，请重试。");
        }
      } else {
        setFormError("暂时无法保存，请重试。");
      }
      setIsSubmitting(false);
    }
  }

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!/^\d{4}-\d{2}-\d{2}$/.test(spentOn)) {
      errors.spent_on = "请选择支出日期。";
    }
    const amountError = validateAmountInput(amount);
    if (amountError) {
      errors.amount = amountError;
    }
    if (!/^[A-Z]{3}$/.test(currency)) {
      errors.currency = "币种必须是三个字母的 ISO 4217 代码。";
    }
    if (!category.trim()) {
      errors.category = "请输入分类。";
    } else if (category.trim().length > MAX_CATEGORY_LENGTH) {
      errors.category = "分类不能超过 80 个字符。";
    }
    if (!description.trim()) {
      errors.description = "请输入说明。";
    } else if (description.length > MAX_DESCRIPTION_LENGTH) {
      errors.description = "说明不能超过 2,000 个字符。";
    }
    return errors;
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit} noValidate>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="expenditure-spent-on">支出日期</label>
        <input
          aria-describedby={fieldErrors.spent_on ? "expenditure-spent-on-error" : undefined}
          aria-invalid={Boolean(fieldErrors.spent_on)}
          className="h-9 rounded-md border bg-background px-3 text-sm"
          id="expenditure-spent-on"
          onInput={(event) => setSpentOn(event.currentTarget.value)}
          type="date"
          value={spentOn}
        />
        {fieldErrors.spent_on ? <p className="text-sm text-destructive" id="expenditure-spent-on-error">{fieldErrors.spent_on}</p> : null}
      </div>
      <div className="grid gap-5 sm:grid-cols-[minmax(0,1fr)_8rem]">
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="expenditure-amount">金额</label>
          <input
            aria-describedby={fieldErrors.amount ? "expenditure-amount-error" : "expenditure-amount-hint"}
            aria-invalid={Boolean(fieldErrors.amount)}
            className="h-9 w-full rounded-md border bg-background px-3 text-sm"
            id="expenditure-amount"
            inputMode="decimal"
            maxLength={19}
            onChange={(event) => setAmount(event.target.value)}
            placeholder="1234.5600"
            type="text"
            value={amount}
          />
          <p className="text-xs text-muted-foreground" id="expenditure-amount-hint">最多四位小数，不输入逗号或符号。</p>
          {fieldErrors.amount ? <p className="text-sm text-destructive" id="expenditure-amount-error">{fieldErrors.amount}</p> : null}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="expenditure-currency">币种</label>
          <input
            aria-describedby={fieldErrors.currency ? "expenditure-currency-error" : undefined}
            aria-invalid={Boolean(fieldErrors.currency)}
            className="h-9 w-full rounded-md border bg-background px-3 text-sm uppercase"
            id="expenditure-currency"
            maxLength={3}
            onChange={(event) => setCurrency(event.target.value.toUpperCase())}
            value={currency}
          />
          {fieldErrors.currency ? <p className="text-sm text-destructive" id="expenditure-currency-error">{fieldErrors.currency}</p> : null}
        </div>
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="expenditure-category">分类</label>
        <input
          aria-describedby={fieldErrors.category ? "expenditure-category-error" : undefined}
          aria-invalid={Boolean(fieldErrors.category)}
          className="h-9 w-full rounded-md border bg-background px-3 text-sm"
          id="expenditure-category"
          maxLength={MAX_CATEGORY_LENGTH}
          onChange={(event) => setCategory(event.target.value)}
          value={category}
        />
        {fieldErrors.category ? <p className="text-sm text-destructive" id="expenditure-category-error">{fieldErrors.category}</p> : null}
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="expenditure-description">说明</label>
        <textarea
          aria-describedby={fieldErrors.description ? "expenditure-description-error" : "expenditure-privacy-hint"}
          aria-invalid={Boolean(fieldErrors.description)}
          className="min-h-48 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm"
          id="expenditure-description"
          maxLength={MAX_DESCRIPTION_LENGTH}
          onChange={(event) => setDescription(event.target.value)}
          value={description}
        />
        <p className="text-xs text-muted-foreground" id="expenditure-privacy-hint">
          只填写必要说明，不记录银行卡号、完整流水号、详细住址、证件或附件。
        </p>
        {fieldErrors.description ? <p className="text-sm text-destructive" id="expenditure-description-error">{fieldErrors.description}</p> : null}
      </div>
      {formError ? <p className="text-sm text-destructive" role="alert">{formError}</p> : null}
      <Button disabled={isSubmitting} type="submit">
        <Save data-icon="inline-start" />
        {isSubmitting ? "正在保存..." : initialExpenditure ? "保存修改" : "记录支出"}
      </Button>
    </form>
  );
}

function changedFields(
  initial: ExpenditureRecord,
  input: ExpenditureCreateInput,
): ExpenditureUpdateInput {
  const changed: ExpenditureUpdateInput = {};
  if (input.spent_on !== initial.spent_on) changed.spent_on = input.spent_on;
  if (canonicalizeAmount(input.amount) !== canonicalizeAmount(initial.amount)) changed.amount = input.amount;
  if (input.currency !== initial.currency) changed.currency = input.currency;
  if (input.category !== initial.category) changed.category = input.category;
  if (input.description !== initial.description) changed.description = input.description;
  return changed;
}

function toFieldErrors(error: ApiRequestError): FieldErrors {
  const allowedFields = new Set<ExpenditureField>([
    "spent_on",
    "amount",
    "currency",
    "category",
    "description",
  ]);
  return error.fieldErrors.reduce<FieldErrors>((errors, fieldError) => {
    const field = fieldError.field.split(".").at(-1) as ExpenditureField | undefined;
    if (field && allowedFields.has(field)) {
      errors[field] = fieldError.message;
    }
    return errors;
  }, {});
}

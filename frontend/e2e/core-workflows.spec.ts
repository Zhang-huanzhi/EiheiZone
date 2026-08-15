import { expect, type Page, test } from "@playwright/test";


const familyLoginName = requiredEnvironment("E2E_FAMILY_LOGIN_NAME");
const familyPassword = requiredEnvironment("E2E_FAMILY_PASSWORD");
const ownerLoginName = requiredEnvironment("E2E_OWNER_LOGIN_NAME");
const ownerPassword = requiredEnvironment("E2E_OWNER_PASSWORD");
const runId = Date.now().toString(36);
const publicPostTitle = `E2E-${runId}-公开近况`;
const familyPostTitle = `E2E-${runId}-家庭近况`;
const familyAuthoredPostTitle = `E2E-${runId}-Family成员近况`;
const ownerQuestion = `E2E-${runId}-Owner问题`;
const ownerAnswer = `E2E-${runId}-Owner区域回答`;
const question = `E2E-${runId}-家庭问题`;
const answer = `E2E-${runId}-当前回答`;
const expenditureCategory = `E2E-${runId}-测试分类`;
const updatedExpenditureCategory = `${expenditureCategory}-已更新`;


test.describe.configure({ mode: "serial" });

test("Public, Family, and Owner complete the v1.1 core workflow", async ({ page }) => {
  await login(page, ownerLoginName, ownerPassword, /\/owner$/);

  await page.getByRole("link", { name: "提出问题" }).click();
  await expect(page).toHaveURL(/\/owner\/qas\/new$/);
  await waitForFormHydration(page, "提交问题");
  await page.getByLabel("问题").fill(ownerQuestion);
  await page.getByRole("button", { name: "提交问题" }).click();
  await expect(page).toHaveURL(/\/owner\/qas\/[0-9a-f-]+$/);
  await expect(page.getByRole("heading", { name: ownerQuestion })).toBeVisible();
  await expect(page.getByText("待回答", { exact: true })).toBeVisible();
  await waitForFormHydration(page, "保存回答");
  await page.getByLabel("回答").fill(ownerAnswer);
  await page.getByRole("button", { name: "保存回答" }).click();
  await expect(page).toHaveURL(/\/owner\/qas$/);
  await expect(page.getByRole("link", { name: new RegExp(ownerQuestion) })).toContainText("已回答");

  await createPost(page, publicPostTitle, "虚构的公开测试正文。", "public");
  await createPost(page, familyPostTitle, "虚构的家庭测试正文。", "family");

  await page.goto("/owner/expenditures/new");
  await waitForFormHydration(page, "记录支出");
  await page.getByLabel("支出日期").fill("2026-07-30");
  await page.getByLabel("金额").fill("1234.5600");
  await page.getByLabel("币种").fill("CNY");
  await page.getByLabel("分类").fill(expenditureCategory);
  await page.getByLabel("说明").fill("虚构的 E2E 重大支出说明。 ");
  await page.getByRole("button", { name: "记录支出" }).click();
  await expect(page).toHaveURL(/\/owner\/expenditures$/);
  await expect(page.getByRole("link", { name: new RegExp(expenditureCategory) })).toBeVisible();

  await logout(page);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "EiheiZone" })).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(publicPostTitle) })).toBeVisible();
  await expect(page.getByText("发布人：E2E Owner")).toBeVisible();
  await expect(page.getByText(familyPostTitle)).toHaveCount(0);

  const privateResponses = await Promise.all([
    page.request.get("/api/v1/qas"),
    page.request.get("/api/v1/expenditures"),
    page.request.get("/api/v1/dashboard"),
  ]);
  for (const response of privateResponses) {
    expect(response.status()).toBe(401);
  }

  await login(page, familyLoginName, familyPassword, /\/family$/);
  await expect(page.getByRole("heading", { name: "最近近况" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "最近问答" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "最近重大支出" })).toBeVisible();
  await expect(page.getByText(publicPostTitle)).toBeVisible();
  await expect(page.getByText(familyPostTitle)).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(expenditureCategory) })).toContainText(
    "CNY 1,234.56",
  );

  await page.goto("/family/qas/new");
  await waitForFormHydration(page, "提交问题");
  await page.getByLabel("问题").fill(question);
  await page.getByRole("button", { name: "提交问题" }).click();
  await expect(page).toHaveURL(/\/family\/qas\/[0-9a-f-]+$/);
  await expect(page.getByRole("heading", { name: question })).toBeVisible();
  await expect(page.getByText("待回答", { exact: true })).toBeVisible();

  await createPost(page, familyAuthoredPostTitle, "Family 成员发布的测试正文。", "family", "family");
  await expect(page.getByRole("link", { name: new RegExp(familyAuthoredPostTitle) })).toBeVisible();
  await expect(page.getByText("发布人：E2E Family")).toBeVisible();

  await page.goto("/owner");
  await expect(page.getByRole("heading", { name: "无权访问管理区域" })).toBeVisible();

  await page.goto("/family");
  await logout(page);

  await login(page, ownerLoginName, ownerPassword, /\/owner$/);
  await expect(page.getByRole("heading", { name: "待回答问题" })).toBeVisible();
  await page.getByRole("link", { name: new RegExp(question) }).click();
  await waitForFormHydration(page, "保存回答");
  await page.getByLabel("回答").fill(answer);
  await page.getByRole("button", { name: "保存回答" }).click();
  await expect(page).toHaveURL(/\/owner\/qas$/);
  await expect(page.getByRole("link", { name: new RegExp(question) })).toContainText("已回答");

  await page.goto("/owner/expenditures");
  await page.getByRole("link", { name: new RegExp(expenditureCategory) }).click();
  await waitForFormHydration(page, "保存修改");
  await page.getByLabel("分类").fill(updatedExpenditureCategory);
  await page.getByRole("button", { name: "保存修改" }).click();
  await expect(page).toHaveURL(/\/owner\/expenditures$/);
  await page.getByRole("link", { name: new RegExp(updatedExpenditureCategory) }).click();
  await expect(page.getByLabel("支出日期")).toHaveValue("2026-07-30");
  await expect(page.getByLabel("金额")).toHaveValue("1234.5600");
  await page.getByRole("button", { name: "删除记录" }).click();
  await page.getByRole("button", { name: "确认删除" }).click();
  await expect(page).toHaveURL(/\/owner\/expenditures$/);
  await expect(page.getByText(updatedExpenditureCategory)).toHaveCount(0);

  await page.goto("/owner/posts");
  await expect(page.getByText("发布人：E2E Family")).toBeVisible();
  await deletePost(page, publicPostTitle);
  await deletePost(page, familyPostTitle);
  await deletePost(page, familyAuthoredPostTitle);

  await page.goto("/family");
  await expect(page.getByRole("heading", { name: "家庭首页" })).toBeVisible();
  await expect(page.getByRole("link", { name: "近况管理" })).toHaveCount(0);
  await logout(page);
  await page.goto("/owner");
  await expect(page).toHaveURL(/\/login/);
});

test("representative pages do not overflow at mobile and desktop viewports", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await expectNoHorizontalOverflow(page);
  await page.goto("/login");
  await expectNoHorizontalOverflow(page);

  await login(page, familyLoginName, familyPassword, /\/family$/);
  for (const path of ["/family", "/family/posts", "/family/qas", "/family/expenditures", "/owner"]) {
    await page.goto(path);
    await expectNoHorizontalOverflow(page);
  }
  await page.goto("/family");
  await logout(page);

  await page.setViewportSize({ width: 1440, height: 900 });
  await login(page, ownerLoginName, ownerPassword, /\/owner$/);
  for (const path of [
    "/owner",
    "/owner/posts",
    "/owner/qas",
    "/owner/qas/new",
    "/owner/expenditures",
    "/owner/posts/new",
  ]) {
    await page.goto(path);
    await expectNoHorizontalOverflow(page);
  }
  await logout(page);
});


async function login(page: Page, loginName: string, password: string, expectedPath: RegExp) {
  await page.goto("/login");
  const submitButton = await waitForFormHydration(page, "登录");
  await page.getByLabel("登录账号").fill(loginName);
  await page.getByLabel("密码").fill(password);
  await submitButton.click();
  await expect(page).toHaveURL(expectedPath);
}

async function logout(page: Page) {
  await page.locator('summary[aria-label$="的账号菜单"]').click();
  const logoutButton = page.getByRole("button", { name: "退出登录" });
  await expect(logoutButton).toBeEnabled();
  await logoutButton.click();
  await expect(page).toHaveURL(/\/$/);
}

async function createPost(
  page: Page,
  title: string,
  body: string,
  visibility: "public" | "family",
  area: "owner" | "family" = "owner",
) {
  const newPostPath = `/${area}/posts/new`;
  const postsPath = `/${area}/posts`;
  await page.goto(newPostPath);
  const submitButton = await waitForFormHydration(page, "发布近况");
  await page.getByLabel("标题").fill(title);
  await page.getByLabel("正文").fill(body);
  await page.getByLabel("可见范围").selectOption(visibility);
  await submitButton.click();
  await expect(page).toHaveURL(new RegExp(`${postsPath.replaceAll("/", "\\/")}$`));
  await expect(page.getByRole("link", { name: new RegExp(title) })).toBeVisible();
}

async function deletePost(page: Page, title: string) {
  await page.getByRole("button", { name: `删除 ${title}` }).click();
  await page.getByRole("button", { name: "确认删除" }).click();
  await expect(page.getByText(title)).toHaveCount(0);
}

async function expectNoHorizontalOverflow(page: Page) {
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      ),
    )
    .toBe(true);
}

async function waitForFormHydration(page: Page, buttonName: string) {
  const submitButton = page.getByRole("button", { name: buttonName });
  await expect(submitButton).toBeEnabled();
  return submitButton;
}

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for Playwright E2E tests`);
  }
  return value;
}

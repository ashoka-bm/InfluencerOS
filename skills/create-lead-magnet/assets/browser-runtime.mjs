export async function loadPuppeteer() {
  const moduleSpecifier = process.env.PUPPETEER_MODULE || 'puppeteer-core';
  const module = await import(moduleSpecifier);
  return module.default;
}

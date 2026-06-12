export function extractPlaceholders(prompt: string): string[] {
  const keys = new Set<string>()
  for (const match of prompt.matchAll(/\{([^}]+)\}/g)) {
    keys.add(match[1])
  }
  return [...keys]
}

export function fillPromptTemplate(
  prompt: string,
  values: Record<string, string | string[]>
): string {
  return prompt.replace(/\{([^}]+)\}/g, (_, key: string) => {
    const value = values[key]
    if (Array.isArray(value)) return value.join('、')
    return value?.trim() ? value : `{${key}}`
  })
}

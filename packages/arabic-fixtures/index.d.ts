export interface Fixture {
  id: string;
  title: string;
  script: string;
  lang: 'ar' | 'fa' | 'he' | string;
  dir: 'rtl' | 'ltr';
  text: string;
  meaning: string;
  checks: string;
  wrap?: boolean;
}

export const fixtures: Fixture[];
export function ids(): string[];
export function get(id: string): Fixture;
export const fontSize: number;
export const wrapWidth: number;
export const version: string;

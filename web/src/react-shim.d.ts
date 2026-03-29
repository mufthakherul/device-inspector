declare module "react" {
  export type ChangeEvent<T = any> = any;
  export const useMemo: (...args: any[]) => any;
  export const useState: (...args: any[]) => any;
  export const StrictMode: any;
  const React: any;
  export default React;
}

declare module "react-dom/client" {
  export const createRoot: any;
}

declare module "react/jsx-runtime" {
  export const Fragment: any;
  export const jsx: any;
  export const jsxs: any;
}

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

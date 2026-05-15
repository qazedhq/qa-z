import type { ReactNode } from "react";

export const metadata = {
  title: "QA-Z Next.js Demo",
  description: "Small deterministic Next.js invoice access demo for QA-Z."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

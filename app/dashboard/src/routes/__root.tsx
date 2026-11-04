import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
  type ErrorComponentProps,
} from "@tanstack/react-router";
import { type ReactNode } from "react";

import appCss from "../styles.css?url";

function NotFoundComponent() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md border border-border bg-card p-8">
        <p className="rotulo">Error 404</p>
        <h1 className="mt-3 text-xl font-semibold">Esta dirección no existe</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          La página que buscas no está publicada o cambió de ruta. El tablero vive en la raíz del
          sitio.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex min-h-11 items-center border border-border-strong px-4 text-sm font-medium hover:bg-accent"
        >
          Ir al tablero
        </Link>
      </div>
    </main>
  );
}

function ErrorComponent({ error, reset }: ErrorComponentProps) {
  console.error(error);
  const router = useRouter();

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md border border-border bg-card p-8">
        <p className="rotulo">Error de la aplicación</p>
        <h1 className="mt-3 text-xl font-semibold">El tablero no pudo cargarse</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Ocurrió una falla al construir la vista. Reintentar vuelve a pedir los datos sin recargar
          la página.
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex min-h-11 items-center border border-border-strong px-4 text-sm font-medium hover:bg-accent"
          >
            Reintentar
          </button>
          <a
            href="/"
            className="inline-flex min-h-11 items-center px-4 text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            Ir al tablero
          </a>
        </div>
      </div>
    </main>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { name: "color-scheme", content: "dark" },
      { name: "robots", content: "noindex" },
      { property: "og:type", content: "website" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      {/* Las rutas hijas se montan aqui. Sin <Outlet /> el tablero no renderiza. */}
      <Outlet />
    </QueryClientProvider>
  );
}

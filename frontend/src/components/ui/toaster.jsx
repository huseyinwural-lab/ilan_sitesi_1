import * as React from "react"
import { useToast as useToastOriginal } from "@/components/ui/use-toast"
import { Toast, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport } from "@/components/ui/toast"

export function Toaster() {
  const { toasts } = useToastOriginal()

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, dismissible = true, ...props }) {
        return (
          <Toast key={id} {...props}>
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && (
                <ToastDescription>{description}</ToastDescription>
              )}
            </div>
            {action}
            {dismissible !== false && <ToastClose />}
          </Toast>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}

export function useToast() {
  return useToastOriginal()
}

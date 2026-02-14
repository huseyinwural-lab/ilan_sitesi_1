import * as React from "react"
import { useToast as useToastOriginal } from "@/components/ui/use-toast"

export function useToast() {
  return useToastOriginal()
}

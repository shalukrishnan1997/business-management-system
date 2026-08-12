import { useEffect, useState } from "react";

import { TextInput } from "@/components/ui/Field";

type Props = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

export function SearchField({ value, onChange, placeholder = "Search…" }: Props) {
  const [local, setLocal] = useState(value);

  useEffect(() => setLocal(value), [value]);

  useEffect(() => {
    const id = window.setTimeout(() => onChange(local), 300);
    return () => window.clearTimeout(id);
  }, [local, onChange]);

  return (
    <TextInput
      value={local}
      onChange={(e) => setLocal(e.target.value)}
      placeholder={placeholder}
      className="max-w-xs bg-surface"
    />
  );
}

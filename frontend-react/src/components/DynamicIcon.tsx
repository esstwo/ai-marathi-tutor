import { icons } from "lucide-react";

interface DynamicIconProps {
  name: string;
  className?: string;
  size?: number;
}

const DynamicIcon = ({ name, className, size }: DynamicIconProps) => {
  // Convert kebab-case to PascalCase
  const pascalName = name
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("") as keyof typeof icons;

  const Icon = icons[pascalName];

  if (!Icon) return null;

  return <Icon className={className} size={size} />;
};

export default DynamicIcon;

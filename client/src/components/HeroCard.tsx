import { Card } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface HeroCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  stats?: Array<{ label: string; value: string }>;
}

export function HeroCard({ title, description, icon: Icon, stats }: HeroCardProps) {
  return (
    <Card className="relative overflow-hidden border-none shadow-2xl">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 opacity-90" />
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20" />
      
      <div className="relative p-8">
        <div className="flex items-start gap-4">
          <div className="bg-white/20 backdrop-blur-sm p-4 rounded-2xl">
            <Icon className="w-10 h-10 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-3xl font-bold text-white mb-2">{title}</h2>
            <p className="text-white/90 text-lg">{description}</p>
            {stats && (
              <div className="flex gap-6 mt-6">
                {stats.map((stat, index) => (
                  <div key={index} className="bg-white/10 backdrop-blur-sm px-4 py-2 rounded-lg">
                    <p className="text-white/70 text-xs">{stat.label}</p>
                    <p className="text-white text-xl font-bold">{stat.value}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

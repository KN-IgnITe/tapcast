import type { ComponentType } from "react";
import type { LucideProps } from "lucide-react";
import {
    Music,
    Trophy,
    Cloud,
    TrendingUp,
    Utensils,
    Calendar,
} from "lucide-react";

interface PredictionFactorItem {
    name: string;
    icon: ComponentType<LucideProps>;
}

interface ActivePredictionFactorsProps {
    title?: string;
    subtitle?: string;
    factors?: PredictionFactorItem[];
}

export function ActivePredictionFactors({
    title = "Active Prediction Factors TEST",
    subtitle = "The following external factors are currently influencing order predictions",
    factors = [
        { name: "Live Music Event", icon: Music },
        { name: "Football Match", icon: Trophy },
        { name: "Warm Weather Forecast", icon: Cloud },
        { name: "Weekend Trend", icon: TrendingUp },
        { name: "Cocktail Special Event", icon: Utensils },
        { name: "Pub Quiz Night", icon: Calendar },
    ],
}: ActivePredictionFactorsProps) {
    return (
        <div className="w-full rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-blue-50 p-6 text-left">
            {/* Header */}
            <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-indigo-600 shadow-md">
                    <TrendingUp size={24} color="#ffffff" />
                </div>

                <div>
                    <h3 className="text-xl font-bold text-gray-900">{title}</h3>
                    <p className="mt-1 text-gray-600">{subtitle}</p>
                </div>
            </div>

            {/* Factor list */}
            <div className="mt-5 flex flex-wrap gap-3">
                {factors.map((factor, index) => {
                    const Icon = factor.icon;

                    return (
                        <div
                            key={index}
                            className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2.5 shadow-sm"
                        >
                            <Icon size={18} color="#6b7280" />
                            <span className="font-medium text-gray-800">
                                {factor.name}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

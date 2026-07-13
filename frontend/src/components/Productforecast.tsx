import { useState } from "react";

interface PredictionFactor {
    name: string;
    weight: number; // percentage
    errorMargin: number; // ±%
    color: string;
}

interface ProductForecastProps {
    plu?: string;
    productName: string;
    category?: string;
    currentForecast: number;
    forecastUnit?: string;
    factors: PredictionFactor[];
    defaultExpanded?: boolean;
}

function ChevronIcon({
    expanded,
    className,
}: {
    expanded: boolean;
    className?: string;
}) {
    return (
        <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            className={`${className} transition-transform duration-200 ${
                expanded ? "" : "rotate-180"
            }`}
            width="20"
            height="20"
        >
            <path
                d="M6 15l6-6 6 6"
                stroke="currentColor"
                strokeWidth="2.25"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

export function ProductForecast({
    plu = "SKU-001",
    productName = "Absolut Vodka",
    category = "1L",
    currentForecast = 1250,
    forecastUnit = "units",
    factors = [
        {
            name: "Pub Quiz Night",
            weight: 15,
            errorMargin: 5.0,
            color: "from-indigo-500 to-indigo-600",
        },
        {
            name: "Historical Base Demand",
            weight: 75,
            errorMargin: 0.9,
            color: "from-blue-400 to-blue-600",
        },
        {
            name: "Weekend Trend",
            weight: 10,
            errorMargin: 1.8,
            color: "from-amber-400 to-amber-500",
        },
    ],
    defaultExpanded = false,
}: ProductForecastProps) {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    const avgErrorMargin =
        factors.reduce((sum, f) => sum + f.errorMargin, 0) / factors.length;

    return (
        <div className="w-full max-w-4xl mx-auto bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
            {/* Header Row - click to expand/collapse */}
            <button
                type="button"
                onClick={() => setIsExpanded((prev) => !prev)}
                className="w-full flex items-center gap-4 p-6 text-left hover:bg-gray-50 transition-colors"
            >
                <ChevronIcon
                    expanded={isExpanded}
                    className="text-gray-400 shrink-0"
                />

                {/* productName, forecast, avg error margin - spread evenly across the row */}
                <div className="flex-1 flex items-center justify-between gap-4">
                    <div className="text-left">
                        <h2 className="text-xl font-bold text-gray-900">
                            {productName}
                            <span className="ml-2 text-gray-500 font-normal text-base">
                                {category}
                            </span>
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">PLU: {plu}</p>
                    </div>

                    <div className="text-center">
                        <div className="text-2xl font-bold text-indigo-600">
                            {currentForecast}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                            {forecastUnit}
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="inline-block px-3 py-1 bg-gray-100 rounded-lg text-lg font-bold text-gray-700">
                            ±{avgErrorMargin.toFixed(1)}%
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                            avg error margin
                        </p>
                    </div>
                </div>
            </button>

            {/* Collapsible: Prediction Composition & Error Margins */}
            {isExpanded && (
                <div className="px-6 pb-6 pt-6 border-t border-gray-200">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                        Prediction Composition & Error Margins
                    </h3>

                    {/* Stacked Bar Chart */}
                    <div className="flex h-14 rounded-xl overflow-hidden shadow-md">
                        {factors.map((factor, index) => (
                            <div
                                key={index}
                                className={`bg-gradient-to-r ${factor.color} transition-all hover:shadow-lg`}
                                style={{ width: `${factor.weight}%` }}
                                title={`${factor.name}: ${factor.weight}%`}
                            />
                        ))}
                    </div>

                    {/* Factor Cards Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                        {factors.map((factor, index) => (
                            <div
                                key={index}
                                className="p-4 bg-gray-50 rounded-xl border border-gray-200 hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div
                                            className={`w-3 h-3 rounded-full bg-gradient-to-r ${factor.color}`}
                                        />
                                        <div>
                                            <p className="font-semibold text-gray-900 text-sm">
                                                {factor.name}
                                            </p>
                                            <p className="text-xs text-gray-600 mt-1">
                                                {factor.weight}%
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold text-red-500 text-sm">
                                            ±{factor.errorMargin}%
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

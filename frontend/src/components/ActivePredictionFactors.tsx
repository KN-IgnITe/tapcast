interface PredictionFactorItem {
    name: string;
    icon: React.ReactNode;
}

function MusicIcon() {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            width="20"
            height="20"
            className="text-gray-500"
        >
            <path
                d="M9 18V5l12-2v13"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <circle
                cx="6"
                cy="18"
                r="3"
                stroke="currentColor"
                strokeWidth="2"
            />
            <circle
                cx="18"
                cy="16"
                r="3"
                stroke="currentColor"
                strokeWidth="2"
            />
        </svg>
    );
}

function TrophyIcon() {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            width="20"
            height="20"
            className="text-gray-500"
        >
            <path
                d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0V4Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <path
                d="M7 5H4a1 1 0 0 0-1 1v1a4 4 0 0 0 4 4M17 5h3a1 1 0 0 1 1 1v1a4 4 0 0 1-4 4"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

function CloudIcon() {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            width="20"
            height="20"
            className="text-gray-500"
        >
            <path
                d="M6.5 19a4.5 4.5 0 0 1-.5-8.97A6 6 0 0 1 17.6 8.02 4.5 4.5 0 0 1 17 19H6.5Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

function TrendingUpIcon({
    className = "text-gray-500",
}: {
    className?: string;
}) {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            width="20"
            height="20"
            className={className}
        >
            <path
                d="M3 17l6-6 4 4 8-8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <path
                d="M15 7h6v6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

function UtensilsIcon() {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            width="20"
            height="20"
            className="text-gray-500"
        >
            <path
                d="M7 3v6a2 2 0 0 0 2 2v10M7 3a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2M11 3v10M17 3c-1.5 0-3 2-3 5s1 5 3 5v8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

function CalendarIcon() {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            width="20"
            height="20"
            className="text-gray-500"
        >
            <rect
                x="3"
                y="5"
                width="18"
                height="16"
                rx="2"
                stroke="currentColor"
                strokeWidth="2"
            />
            <path
                d="M3 10h18M8 3v4M16 3v4"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

interface ActivePredictionFactorsProps {
    title?: string;
    subtitle?: string;
    factors?: PredictionFactorItem[];
}

export function ActivePredictionFactors({
    title = "Active Prediction Factors",
    subtitle = "The following external factors are currently influencing order predictions",
    factors = [
        { name: "Live Music Event", icon: <MusicIcon /> },
        { name: "Football Match", icon: <TrophyIcon /> },
        { name: "Warm Weather Forecast", icon: <CloudIcon /> },
        { name: "Weekend Trend", icon: <TrendingUpIcon /> },
        { name: "Cocktail Special Event", icon: <UtensilsIcon /> },
        { name: "Pub Quiz Night", icon: <CalendarIcon /> },
    ],
}: ActivePredictionFactorsProps) {
    return (
        <div className="w-full rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-blue-50 p-6 text-left">
            {/* Header */}
            <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-indigo-600 shadow-md">
                    <TrendingUpIcon className="text-white" />
                </div>

                <div>
                    <h3 className="text-xl font-bold text-gray-900">{title}</h3>
                    <p className="mt-1 text-gray-600">{subtitle}</p>
                </div>
            </div>

            {/* Factor list */}
            <div className="mt-5 flex flex-wrap gap-3">
                {factors.map((factor, index) => (
                    <div
                        key={index}
                        className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2.5 shadow-sm"
                    >
                        {factor.icon}
                        <span className="font-medium text-gray-800">
                            {factor.name}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

import { useState } from "react";
import { DayPicker, type DateRange } from "react-day-picker";

export default function DateRangePicker() {
    const [range, setRange] = useState<DateRange | undefined>();

    return (
        <DayPicker
            mode="range"
            selected={range}
            onSelect={setRange}
            classNames={{
                caption_label: "text-sm font-semibold text-gray-800",
                nav: "flex items-center gap-1",
                button_previous:
                    "w-8 h-8 p-0 flex items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors",
                button_next:
                    "w-8 h-8 p-0 flex items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors",

                weekday:
                    "h-10 text-[11px] font-semibold uppercase tracking-wider text-gray-400 text-center align-middle",

                day_button:
                    "w-7 h-7 m-1 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-all flex items-center justify-center focus:outline-none",
            }}
            modifiersClassNames={{
                selected: "bg-indigo-100 text-white font-semibold",
                range_start: "rounded-l-xl rounded-r-none transition-all",
                range_end: "rounded-r-xl rounded-l-none transition-all",
                range_middle:
                    "bg-indigo-50 text-indigo-900 rounded-none hover:bg-indigo-100 transition-all",
                today: "text-indigo-600 font-bold relative after:absolute after:bottom-1.25 after:left-4 after:w-1 after:h-1 after:bg-indigo-600 after:rounded-full",
            }}
        />
    );
}

import { useState } from "react";
import {
    ChevronLeft,
    ChevronRight,
    BarChart2,
    Upload,
    Settings,
} from "lucide-react";
import Dashboard from "./dashboard/Dashboard";

export default function Shell() {
    const [isOpen, setIsOpen] = useState(true);

    const menuItems = [
        { icon: <BarChart2 size={20} />, label: "Dashboard" },
        { icon: <Upload size={20} />, label: "Data" },
        { icon: <Settings size={20} />, label: "Settings" },
    ];

    return (
        <>
            <div className="flex min-h-screen bg-gray-50">
                <aside
                    className={`bg-white border-r border-gray-200 flex flex-col justify-between transition-all duration-300 ease-in-out ${isOpen ? "w-64" : "w-18"}`}
                >
                    <div>
                        {/* header */}
                        <div className="flex mx-3 items-center justify-between h-16 border-b border-gray-100">
                            <div
                                className={`flex mx-2 gap-2 font-semibold text-lg transition-opacity duration-200 ${isOpen ? "opacity-100" : "opacity-0 hidden"}`}
                            >
                                <span>TapCast</span>
                            </div>

                            <button
                                onClick={() => setIsOpen(!isOpen)}
                                className="p-3 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-600 dynamic-toggle"
                            >
                                {isOpen ? (
                                    <ChevronLeft size={20} />
                                ) : (
                                    <ChevronRight size={20} />
                                )}
                            </button>
                        </div>

                        {/* tabs */}
                        <nav className="p-3 space-y-1">
                            {menuItems.map((item, index) => (
                                <a
                                    key={index}
                                    href="#"
                                    className="flex items-center p-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors group relative"
                                >
                                    <div className="shrink-0">{item.icon}</div>

                                    <span
                                        className={`ml-3 transition-all duration-300 whitespace-nowrap ${isOpen ? "opacity-100" : "opacity-0 w-0 overflow-hidden"}`}
                                    >
                                        {item.label}
                                    </span>

                                    {isOpen || (
                                        <div className="absolute left-full ml-4 rounded-md px-2 py-1 bg-gray-900 text-white text-xs invisible opacity-0 -translate-x-2 transition-all group-hover:visible group-hover:opacity-100 group-hover:translate-x-0 z-50 whitespace-nowrap">
                                            {item.label}
                                        </div>
                                    )}
                                </a>
                            ))}
                        </nav>
                    </div>
                </aside>
                <Dashboard></Dashboard>
            </div>
        </>
    );
}

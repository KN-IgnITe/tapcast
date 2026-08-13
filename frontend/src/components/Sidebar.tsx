import {
    useState,
    type Dispatch,
    type ReactNode,
    type SetStateAction,
} from "react";
import {
    ChevronLeft,
    ChevronRight,
    BarChart2,
    Upload,
    Settings,
} from "lucide-react";

type TabItem = { icon: ReactNode; label: string };

interface SidebarHeaderProps {
    isOpen: boolean;
    setIsOpen: Dispatch<SetStateAction<boolean>>;
}

function SidebarHeader({ isOpen, setIsOpen }: SidebarHeaderProps) {
    return (
        <>
            <div className="flex p-3 items-center justify-between h-16">
                <div
                    className={`flex font-semibold text-lg transition-all duration-300 whitespace-nowrap overflow-hidden ${isOpen ? "opacity-100 max-w-xs mx-2" : "opacity-0 max-w-0 mx-0"}`}
                >
                    <span>TapCast</span>
                </div>

                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={`flex items-center justify-center h-12 rounded-xl hover:bg-gray-200 transition-colors text-gray-600 w-12 cursor-pointer`}
                >
                    {isOpen ? (
                        <ChevronLeft size={20} />
                    ) : (
                        <ChevronRight size={20} />
                    )}
                </button>
            </div>
        </>
    );
}

interface TabProps {
    tabItem: TabItem;
    index: number;
    isSidebarOpen: boolean;
}

function Tab({ tabItem, index, isSidebarOpen }: TabProps) {
    return (
        <a
            key={index}
            href="#"
            className="flex items-center p-3 rounded-xl text-gray-600 hover:bg-gray-200 transition-colors group relative"
        >
            {/* icon */}
            <div className="flex items-center justify-center shrink-0 border-2 border-transparent">
                {tabItem.icon}
            </div>

            {/* label */}
            <span
                className={`flex transition-all duration-300 whitespace-nowrap overflow-hidden ${isSidebarOpen ? "opacity-100 max-w-xs mx-2" : "opacity-0 max-w-0 mx-0"}`}
            >
                {tabItem.label}
            </span>

            {/* hover label */}
            {isSidebarOpen || (
                <div className="absolute left-full ml-4 rounded-md px-2 py-1 bg-gray-900 text-white text-xs invisible opacity-0 -translate-x-2 transition-all group-hover:visible group-hover:opacity-100 group-hover:translate-x-0 z-50 whitespace-nowrap">
                    {tabItem.label}
                </div>
            )}
        </a>
    );
}

export default function Sidebar() {
    const [isOpen, setIsOpen] = useState(true);

    const tabItems = [
        { icon: <BarChart2 size={20} />, label: "Dashboard" },
        { icon: <Upload size={20} />, label: "Data" },
        { icon: <Settings size={20} />, label: "Settings" },
    ];

    return (
        <>
            <aside
                className={`bg-gray-50 border-r border-gray-200 flex flex-col justify-between transition-all duration-300 ease-in-out ${isOpen ? "w-64" : "w-18"}`}
            >
                <div>
                    <SidebarHeader isOpen={isOpen} setIsOpen={setIsOpen} />

                    <nav className="p-3 space-y-1">
                        {tabItems.map((item, index) => (
                            <Tab
                                tabItem={item}
                                index={index}
                                isSidebarOpen={isOpen}
                            />
                        ))}
                    </nav>
                </div>
            </aside>
        </>
    );
}

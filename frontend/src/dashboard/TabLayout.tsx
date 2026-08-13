import type { ReactNode } from "react";
import Header from "../components/Header";

interface TitledScrollingLayoutProps {
    header: string;
    children: ReactNode;
}

export default function TabLayout({
    header,
    children,
}: TitledScrollingLayoutProps) {
    return (
        <>
            <div className="flex flex-col h-screen w-full overflow-hidden">
                <Header text={header} />

                <div className="flex-1 overflow-y-auto">
                    <div className="w-4xl px-8 mx-auto my-8 space-y-8 text-gray-900">
                        {children}
                    </div>
                </div>
            </div>
        </>
    );
}

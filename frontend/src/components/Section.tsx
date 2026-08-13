import type { ReactNode } from "react";

interface SectionProps {
    title: string;
    children: ReactNode;
}

export default function Section({ title, children }: SectionProps) {
    return (
        <>
            <section className="bg-white border border-gray-200/80 rounded-2xl p-5 shadow-sm space-y-3">
                <h2 className="text-xs font-semibold tracking-wider text-gray-400">
                    {title}
                </h2>

                {children}
            </section>
        </>
    );
}

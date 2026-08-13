interface HeaderProps {
    text: string;
}

export default function Header({ text }: HeaderProps) {
    return (
        <>
            <header className="flex p-3 items-center h-16 border-b border-gray-200 bg-gray-50">
                <h1 className="text-lg ml-4 my-4 font-semibold text-gray-900">
                    {text}
                </h1>
            </header>
        </>
    );
}

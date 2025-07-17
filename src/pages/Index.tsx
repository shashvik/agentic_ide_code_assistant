import { useState } from "react";
import { Code, Zap, Brain, Settings, User, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatPanel } from "@/components/ChatPanel";
import { CodeEditor } from "@/components/CodeEditor";
import { ResizablePanel } from "@/components/ResizablePanel";

const Index = () => {
  const [code, setCode] = useState(`// Welcome to Vyasa IDE
// An AI-powered coding environment

console.log("Hello, World!");

function greetUser(name) {
  return \`Welcome to Vyasa, \${name}!\`;
}

// Try asking the AI assistant to generate code for you
const message = greetUser("Developer");
console.log(message);`);
  
  const [language, setLanguage] = useState("javascript");
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const handleCodeGenerate = (newCode: string, newLanguage: string) => {
    setCode(newCode);
    setLanguage(newLanguage);
  };

  const toggleTheme = () => {
    setTheme(prev => prev === "dark" ? "light" : "dark");
  };

  return (
    <div className="h-screen w-full bg-background flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-panel-border bg-gradient-subtle">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center">
              <Code className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-primary bg-clip-text text-transparent">
               Vyasa IDE
              </h1>
              <p className="text-xs text-muted-foreground">AI-Powered Development Environment</p>
            </div>
          </div>
          
          <div className="flex items-center gap-1 ml-4">
            <div className="flex items-center gap-1 px-2 py-1 bg-accent/20 rounded-full">
              <Zap className="w-3 h-3 text-accent" />
              <span className="text-xs font-medium text-accent">AI Enabled</span>
            </div>
            <div className="flex items-center gap-1 px-2 py-1 bg-primary/20 rounded-full">
              <Brain className="w-3 h-3 text-primary" />
              <span className="text-xs font-medium text-primary">Smart Code</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={toggleTheme}>
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="sm">
            <Settings className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <User className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <ResizablePanel
          leftPanel={
            <ChatPanel onCodeGenerate={handleCodeGenerate} />
          }
          rightPanel={
            <CodeEditor
              code={code}
              language={language}
              onCodeChange={setCode}
              onLanguageChange={setLanguage}
            />
          }
          defaultLeftWidth={420}
          minLeftWidth={320}
          maxLeftWidth={600}
        />
      </div>

      {/* Footer */}
      <footer className="flex items-center justify-between px-6 py-2 border-t border-panel-border bg-code-bg/50">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>Ready</span>
          <span>•</span>
          <span>Language: {language}</span>
          <span>•</span>
          <span>Lines: {code.split('\n').length}</span>
        </div>
        
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>Built with ❤️ using React & AI</span>
        </div>
      </footer>
    </div>
  );
};

export default Index;

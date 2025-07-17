import { useState, useEffect } from "react";
import { 
  Play, 
  Square, 
  Download, 
  Copy, 
  FolderOpen, 
  File, 
  Terminal,
  ChevronRight,
  ChevronDown,
  FileCode,
  Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import io from "socket.io-client";

interface CodeEditorProps {
  code: string;
  language: string;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: string) => void;
}

interface FileItem {
  id: string;
  name: string;
  type: "file" | "folder";
  content?: string;
  language?: string;
  children?: FileItem[];
}

export function CodeEditor({ code, language, onCodeChange, onLanguageChange }: CodeEditorProps) {
  const [output, setOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);

  const fetchFiles = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/files");
      const data = await response.json();
      setFiles(data);
    } catch (error) {
      console.error("Error fetching files:", error);
    }
  };

  useEffect(() => {
    fetchFiles();

    const socket = io("http://localhost:5000");
    socket.on("file_change", () => {
      fetchFiles();
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const toggleFolder = (folderId: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
  };

  const selectFile = async (file: FileItem) => {
    if (file.type === "file") {
      try {
        const response = await fetch(`http://localhost:5000/api/files/${file.id}`);
        const data = await response.json();
        const updatedFile = { ...file, content: data.content };
        setSelectedFile(updatedFile);
        onCodeChange(data.content);
        if (file.language) {
          onLanguageChange(file.language);
        }
      } catch (error) {
        console.error("Error fetching file content:", error);
      }
    }
  };

  const renderFileTree = (items: FileItem[], level = 0) => {
    return items.map(item => (
      <div key={item.id} style={{ paddingLeft: `${level * 12}px` }}>
        <div
          className={cn(
            "flex items-center gap-2 py-1 px-2 hover:bg-secondary/50 cursor-pointer rounded text-sm",
            selectedFile?.id === item.id && item.type === "file" && "bg-secondary"
          )}
          onClick={() => item.type === "folder" ? toggleFolder(item.id) : selectFile(item)}
        >
          {item.type === "folder" ? (
            <>
              {expandedFolders.has(item.id) ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
              <FolderOpen className="w-3 h-3 text-accent" />
            </>
          ) : (
            <>
              <div className="w-3" />
              <FileCode className="w-3 h-3 text-primary" />
            </>
          )}
          <span className="truncate">{item.name}</span>
        </div>
        {item.type === "folder" && expandedFolders.has(item.id) && item.children && (
          <div>
            {renderFileTree(item.children, level + 1)}
          </div>
        )}
      </div>
    ));
  };

  const runCode = async () => {
    setIsRunning(true);
    setOutput("Running code...\n");

    try {
      const response = await fetch("http://localhost:5000/api/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          code: selectedFile?.content || code, 
          language 
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setOutput(data.output);
      } else {
        setOutput(`Error: ${data.error}`);
      }
    } catch (error) {
      setOutput("An unexpected error occurred. Please check the console.");
      console.error("Error running code:", error);
    } finally {
      setIsRunning(false);
    }
  };

  const copyCode = () => {
    navigator.clipboard.writeText(selectedFile?.content || code);
  };

  const downloadCode = () => {
    const element = document.createElement("a");
    const file = new Blob([selectedFile?.content || code], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = selectedFile?.name || `main.${language === "python" ? "py" : "js"}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="flex h-full bg-editor-bg">
      {/* File Explorer */}
      <div className="w-64 border-r border-panel-border bg-code-bg">
        <div className="p-3 border-b border-panel-border">
          <div className="flex items-center gap-2">
            <File className="w-4 h-4 text-accent" />
            <span className="font-medium text-sm">Explorer</span>
          </div>
        </div>
        <ScrollArea className="h-[calc(100%-60px)]">
          <div className="p-2">
            {renderFileTree(files)}
          </div>
        </ScrollArea>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between p-3 border-b border-panel-border bg-code-bg/50">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium">
                {selectedFile?.name || `main.${language === "python" ? "py" : "js"}`}
              </span>
            </div>
            <Select value={language} onValueChange={onLanguageChange}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="javascript">JavaScript</SelectItem>
                <SelectItem value="python">Python</SelectItem>
                <SelectItem value="html">HTML</SelectItem>
                <SelectItem value="css">CSS</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={copyCode}>
              <Copy className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={downloadCode}>
              <Download className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <Settings className="w-4 h-4" />
            </Button>
            <Button 
              onClick={runCode} 
              disabled={isRunning}
              className="bg-gradient-primary hover:opacity-90"
            >
              {isRunning ? (
                <Square className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {isRunning ? "Stop" : "Run"}
            </Button>
          </div>
        </div>

        {/* Editor and Output */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 relative">
            <textarea
              value={selectedFile?.content || code}
              onChange={(e) => {
                const newCode = e.target.value;
                onCodeChange(newCode);
                if (selectedFile) {
                  setSelectedFile({
                    ...selectedFile,
                    content: newCode
                  });
                }
              }}
              className="w-full h-full p-4 bg-transparent text-foreground font-mono text-sm leading-relaxed resize-none focus:outline-none"
              style={{ 
                tabSize: 2,
                lineHeight: "1.6"
              }}
              spellCheck={false}
              placeholder={`Start coding in ${language}...`}
            />
          </div>

          {/* Output Panel */}
          <div className="h-48 border-t border-panel-border">
            <Tabs defaultValue="console" className="h-full">
              <TabsList className="grid w-full grid-cols-2 bg-console-bg">
                <TabsTrigger value="console" className="flex items-center gap-2">
                  <Terminal className="w-3 h-3" />
                  Console
                </TabsTrigger>
                <TabsTrigger value="preview">Preview</TabsTrigger>
              </TabsList>
              
              <TabsContent value="console" className="h-full mt-0">
                <ScrollArea className="h-full">
                  <div className="p-4 bg-console-bg">
                    <pre className="font-mono text-xs text-green-400 whitespace-pre-wrap">
                      {output || "Ready to run your code. Click the Run button to execute."}
                    </pre>
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="preview" className="h-full mt-0">
                <div className="h-full bg-background border-l border-panel-border p-4">
                  <div className="text-center text-muted-foreground">
                    <FileCode className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Live preview will appear here</p>
                    <p className="text-xs mt-1">Run your code to see the output</p>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}
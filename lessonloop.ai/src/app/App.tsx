import { useState, useRef } from "react";
import { Sparkles, Copy, Mail, Settings, Upload, CheckCircle2, GripVertical } from "lucide-react";

const PLACEHOLDER_EMAIL = `Hi [Student Name],

I hope this message finds you well! I wanted to share a quick update on today's lesson.

📚 今天學了什麼？
✅ Great Progress: You showed strong understanding of the core concepts introduced in today's session. She was engaged and asked thoughtful questions throughout.
✅ Key Topics Covered:
  • Introduction to fractions and equivalent values
  • Visual models for comparing fractions
  • Real-world examples using food and measurements

🌟 給你的小鼓勵: You confidently completed the first two exercises on your own and only needed minor guidance on the third. That's a real improvement from last week!

🏡 Homework: [Homework Topic]

Looking forward to our next lesson. Please don't hesitate to reach out if you have any questions! 

Warm regards,
[Teacher's name]
via LessonLoop AI Assistant 🎓`;

export default function App() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [studentName, setStudentName] = useState("");
  const [studentEmail, setStudentEmail] = useState("");
  const [teacherName, setTeacherName] = useState("");
  const [emailText, setEmailText] = useState(PLACEHOLDER_EMAIL);
  const [isGenerating, setIsGenerating] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) setUploadedFile(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setUploadedFile(file);
  };

  const handleGenerate = async () => {
    if (!uploadedFile) {
      alert("Please upload a file first.");
      return;
    }

    setIsGenerating(true);
    setHasGenerated(false);

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('student_name', studentName);
    formData.append('student_email', studentEmail);
    formData.append('teacher_name', teacherName);

    try {
      // Use environment variable for API URL, fallback to localhost for development
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5001';
      const response = await fetch(`${apiUrl}/api/process-lesson`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate summary');
      }

      const data = await response.json();
      setEmailText(data.email);
      setHasGenerated(true);
    } catch (error) {
      console.error("Error generating summary:", error);
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(emailText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleGmail = () => {
    const emailSubject = encodeURIComponent(`Lesson Summary – ${studentName || "Student"}`);
    const body = encodeURIComponent(emailText);
    window.open(`https://mail.google.com/mail/?view=cm&su=${emailSubject}&body=${body}`, "_blank");
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top Nav */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="text-gray-900 tracking-tight">
            <span style={{ fontWeight: 700 }}>LessonLoop</span>{" "}
            <span className="text-indigo-600" style={{ fontWeight: 600 }}>AI</span>
          </span>
        </div>
        <button className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
          <Settings className="w-5 h-5" />
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:flex-row gap-0 lg:gap-6 p-4 lg:p-8 max-w-7xl mx-auto w-full">
        {/* Left Column – Input Zone */}
        <div className="w-full lg:w-[420px] flex-shrink-0 flex flex-col gap-5">
          <div>
            <h1 className="text-gray-900 mb-1" style={{ fontWeight: 700 }}>Create Lesson Summary</h1>
            <p className="text-gray-500 text-sm">Upload a lesson recording and generate a personalised lesson summary email in seconds.</p>
          </div>

          {/* Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed cursor-pointer transition-all py-10 px-6 text-center
              ${isDragging
                ? "border-indigo-400 bg-indigo-50"
                : uploadedFile
                  ? "border-green-400 bg-green-50"
                  : "border-gray-300 bg-white hover:border-indigo-300 hover:bg-indigo-50/40"
              }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*,audio/*"
              className="hidden"
              onChange={handleFileInput}
            />
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${uploadedFile ? "bg-green-100" : "bg-gray-100"}`}>
              {uploadedFile
                ? <CheckCircle2 className="w-6 h-6 text-green-500" />
                : <Upload className="w-6 h-6 text-gray-400" />
              }
            </div>
            {uploadedFile ? (
              <>
                <p className="text-green-700 text-sm" style={{ fontWeight: 600 }}>{uploadedFile.name}</p>
                <p className="text-green-600 text-xs">File ready · Click to replace</p>
              </>
            ) : (
              <>
                <p className="text-gray-700 text-sm" style={{ fontWeight: 600 }}>Drop Lesson Video or Audio Here</p>
                <p className="text-gray-400 text-xs">Supports MP4, MOV, MP3, WAV · or click to browse</p>
              </>
            )}
          </div>

          {/* Form Fields */}
          <div className="bg-white rounded-2xl border border-gray-200 p-5 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm text-gray-600" style={{ fontWeight: 500 }}>Student Name</label>
              <input
                type="text"
                placeholder="e.g. Sarah Johnson"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm text-gray-600" style={{ fontWeight: 500 }}>Student Email</label>
              <input
                type="email"
                placeholder="e.g. student@email.com"
                value={studentEmail}
                onChange={(e) => setStudentEmail(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm text-gray-600" style={{ fontWeight: 500 }}>Teacher Name</label>
              <input
                type="text"
                placeholder="e.g. Ms. Davis"
                value={teacherName}
                onChange={(e) => setTeacherName(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all"
              />
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full flex items-center justify-center gap-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-70 disabled:cursor-not-allowed text-white py-3.5 px-6 transition-all shadow-sm shadow-indigo-200"
          >
            {isGenerating ? (
              <>
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                <span className="text-sm" style={{ fontWeight: 600 }}>Generating…</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span className="text-sm" style={{ fontWeight: 600 }}>Generate Lesson Summary</span>
              </>
            )}
          </button>

          {/* Tips */}
          <div className="bg-indigo-50 rounded-2xl px-4 py-3.5 border border-indigo-100">
            <p className="text-xs text-indigo-700" style={{ fontWeight: 600 }}>💡 Tips for best results</p>
            <ul className="mt-1.5 space-y-1 text-xs text-indigo-600">
              <li>• Upload clear audio for accurate transcription</li>
              <li>• Include student name for personalised emails</li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="hidden lg:flex items-center justify-center">
          <div className="h-full w-px bg-gray-200" />
        </div>

        {/* Right Column – Output Zone */}
        <div className="flex-1 flex flex-col gap-4 mt-4 lg:mt-0">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-gray-900" style={{ fontWeight: 700 }}>Email Draft</h2>
              <p className="text-gray-500 text-sm">Review and edit before sending.</p>
            </div>
            {isGenerating && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs text-amber-700" style={{ fontWeight: 500 }}>
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block animate-pulse" />
                In process
              </span>
            )}
            {!isGenerating && hasGenerated && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 border border-green-200 px-3 py-1 text-xs text-green-700" style={{ fontWeight: 500 }}>
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
                Ready to send
              </span>
            )}
          </div>

          {/* Email Draft Card */}
          <div className="flex-1 bg-white rounded-2xl border border-gray-200 shadow-sm flex flex-col overflow-hidden">
            {/* Email toolbar */}
            <div className="flex items-center gap-3 px-5 py-3.5 border-b border-gray-100 bg-gray-50/60">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-300" />
                <div className="w-3 h-3 rounded-full bg-yellow-300" />
                <div className="w-3 h-3 rounded-full bg-green-300" />
              </div>
              <div className="flex-1 flex items-center gap-2 bg-white rounded-lg border border-gray-200 px-3 py-1.5">
                <Mail className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <span className="text-xs text-gray-400 truncate">
                  To: {studentEmail || "students@email.com"}
                </span>
              </div>
              <div className="flex-1 hidden sm:flex items-center gap-2 bg-white rounded-lg border border-gray-200 px-3 py-1.5">
                <span className="text-xs text-gray-400 truncate">Subject: Lesson Summary – {studentName || "Student"}</span>
              </div>
            </div>

            {/* Editable area */}
            <textarea
              value={emailText}
              onChange={(e) => setEmailText(e.target.value)}
              className="flex-1 w-full resize-none p-6 text-sm text-gray-700 leading-relaxed outline-none bg-white placeholder-gray-300 min-h-[340px]"
              spellCheck
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleCopy}
              className={`flex-1 flex items-center justify-center gap-2 rounded-2xl border py-3 px-5 text-sm transition-all
                ${copied
                  ? "border-green-300 bg-green-50 text-green-700"
                  : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300"
                }`}
            >
              {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              <span style={{ fontWeight: 500 }}>{copied ? "Copied!" : "Copy to Clipboard"}</span>
            </button>
            <button
              onClick={handleGmail}
              className="flex-1 flex items-center justify-center gap-2 rounded-2xl border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 py-3 px-5 text-sm transition-all"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
                <path d="M22 6C22 4.9 21.1 4 20 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6ZM20 6L12 11L4 6H20ZM20 18H4V8L12 13L20 8V18Z" fill="#EA4335"/>
              </svg>
              <span style={{ fontWeight: 500 }}>Open in Gmail</span>
            </button>
          </div>

          {/* Footer note */}
          <p className="text-xs text-gray-400 text-center pb-1">
            All emails are generated locally · Nothing is stored or shared · LessonLoop AI
          </p>
        </div>
      </main>
    </div>
  );
}
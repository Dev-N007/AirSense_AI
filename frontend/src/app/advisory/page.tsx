"use client";

import React, { useState, useEffect } from "react";

const FALLBACK_ADVISORY = {
  station_name: "Anand Vihar, Delhi - CPCB",
  predicted_aqi_24h: 395,
  citizen_advisory_en: "Air quality is Very Poor. Health warnings of emergency conditions are active. Everyone, especially children, the elderly, and those with pre-existing heart or lung diseases, should avoid all outdoor physical activities. Mandatorily wear N95 masks when stepping outdoors. Keep all windows shut, run indoor air purifiers on high speed, and strictly avoid going outdoors.",
  citizen_advisory_hi: "वायु गुणवत्ता बहुत खराब (अति गंभीर) श्रेणी में है। स्वास्थ्य आपातकाल की चेतावनी सक्रिय है। सभी लोग, विशेष रूप से बच्चे, बुजुर्ग और हृदय या फेफड़ों की बीमारी से पीड़ित व्यक्ति, बाहर किसी भी प्रकार की शारीरिक गतिविधि से बचें। बाहर निकलते समय अनिवार्य रूप से N95 मास्क पहनें। घर की सभी खिड़कियां बंद रखें, इंडोर एयर प्यूरीफायर चलाएं और बाहर जाने से पूरी तरह बचें।",
  timestamp: new Date().toISOString()
};

export default function AdvisoryPage() {
  const [advisory, setAdvisory] = useState<any>(FALLBACK_ADVISORY);
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [apiSource, setApiSource] = useState("Local Simulation Cache");

  useEffect(() => {
    fetch("http://localhost:8000/api/advisory")
      .then(res => {
        if (!res.ok) throw new Error("API Offline");
        return res.json();
      })
      .then(data => {
        if (data && data.length > 0) {
          setAdvisory(data[0]);
          setApiSource("Live Gemini 2.5 Flash Agent");
        }
      })
      .catch(err => {
        console.log("Using cached fallback advisory bulletin: ", err.message);
        setApiSource("Local Simulation Cache");
      });
  }, []);

  const contentText = lang === "en" ? advisory.citizen_advisory_en : advisory.citizen_advisory_hi;
  
  const guidelines = lang === "en" ? [
    { title: "😷 N95 Mask Mandatory", desc: "Standard cloth masks do not filter PM2.5 particles. Always wear N95/N99 respirators when outdoors." },
    { title: "🏠 Stay Indoors", desc: "Close windows to prevent outdoor polluted air leakage. Keep indoor ventilation off." },
    { title: "🌬️ Air Purifier", desc: "Operate indoor HEPA air purifiers at high speed in bedrooms and common living areas." },
    { title: "🧘 No Outdoor Workouts", desc: "Avoid jogging, cycling, or intense exercises outside. Transition workouts to indoor gym settings." }
  ] : [
    { title: "😷 N95 मास्क अनिवार्य", desc: "सामान्य कपड़े के मास्क PM2.5 कणों को फिल्टर नहीं कर पाते। बाहर निकलते समय हमेशा N95/N99 रेस्पिरेटर पहनें।" },
    { title: "🏠 घर के अंदर रहें", desc: "प्रदूषित बाहरी हवा को अंदर आने से रोकने के लिए खिड़कियां बंद रखें। वेंटिलेशन बंद रखें।" },
    { title: "🌬️ एयर प्यूरीफायर चलाएं", desc: "बेडरूम और रहने के सामान्य कमरों में इंडोर HEPA एयर प्यूरीफायर को हाई स्पीड पर चलाएं।" },
    { title: "🧘 बाहरी व्यायाम न करें", desc: "बाहर टहलने, साइकिल चलाने या भारी व्यायाम से बचें। घर के अंदर ही योग या कसरत करें।" }
  ];

  const vulnerables = lang === "en" ? [
    { target: "🧒 Children", risk: "Underdeveloped lungs inhale more air relative to body weight.", action: "Keep children indoors. Do not let them play outdoors." },
    { target: "👵 Seniors", risk: "Highly susceptible to cardiovascular stress and respiratory issues.", action: "Avoid morning/evening walks. Keep emergency inhalers handy." },
    { target: "🫁 Asthmatics", risk: "Extreme PM2.5 levels trigger sudden asthma attacks and bronchospasm.", action: "Take preventative dosages. Limit triggers. Stay near air purifiers." }
  ] : [
    { target: "🧒 बच्चे", risk: "अपूर्ण रूप से विकसित फेफड़े शरीर के वजन की तुलना में अधिक हवा सांस में लेते हैं।", action: "बच्चों को घर के अंदर रखें। उन्हें बाहर न खेलने दें।" },
    { target: "👵 बुजुर्ग", risk: "हृदय संबंधी तनाव और श्वसन समस्याओं के प्रति अत्यधिक संवेदनशील।", action: "सुबह/शाम की सैर से बचें। आपातकालीन इनहेलर साथ रखें।" },
    { target: "🫁 दमा रोगी", risk: "PM2.5 का अत्यधिक स्तर अचानक अस्थमा के दौरे का कारण बन सकता है।", action: "नियमित दवाएं लें। प्रदूषण के कारकों से बचें। प्यूरीफायर के पास रहें।" }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="font-heading font-bold text-3xl text-slate-100">
            {lang === "en" ? "Citizen Health Advisory" : "नागरिक स्वास्थ्य परामर्श"}
          </h2>
          <p className="text-slate-400 text-sm">
            {lang === "en" 
              ? "Bilingual health recommendations and alert bulletins generated for Delhi residents."
              : "दिल्ली के नागरिकों के लिए जारी स्वास्थ्य निर्देश और सूचना बुलेटिन।"}
          </p>
        </div>

        {/* Language Toggler & Source */}
        <div className="flex items-center gap-4">
          <div className="flex rounded-lg bg-slate-900 border border-slate-800 p-1">
            <button 
              onClick={() => setLang("en")}
              className={`px-3 py-1 rounded text-xs font-bold transition-all duration-150 ${lang === "en" ? "bg-emerald-500 text-white" : "text-slate-400 hover:text-slate-200"}`}
            >
              English
            </button>
            <button 
              onClick={() => setLang("hi")}
              className={`px-3 py-1 rounded text-xs font-bold transition-all duration-150 ${lang === "hi" ? "bg-emerald-500 text-white" : "text-slate-400 hover:text-slate-200"}`}
            >
              हिन्दी
            </button>
          </div>
          <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700/60">
            Source: <span className="font-bold text-emerald-400">{apiSource}</span>
          </span>
        </div>
      </div>

      {/* Main Advisory Box */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-md">
        <h3 className="font-heading font-bold text-base text-slate-200 mb-4 flex items-center gap-2">
          <span>📢</span> {lang === "en" ? "Active Public Health Bulletin" : "सक्रिय जन स्वास्थ्य बुलेटिन"}
        </h3>
        
        <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800/80 text-base leading-relaxed text-slate-200 font-medium">
          {contentText}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Core Preventative Guidelines */}
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/20 backdrop-blur-md">
          <h3 className="font-heading font-bold text-lg text-slate-200 mb-6">
            {lang === "en" ? "General Prevention Rules" : "सामान्य बचाव नियम"}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {guidelines.map((g, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/60">
                <h4 className="font-heading font-bold text-sm text-slate-200">{g.title}</h4>
                <p className="text-slate-400 text-xs mt-2 leading-relaxed">{g.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Vulnerable Groups */}
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/20 backdrop-blur-md">
          <h3 className="font-heading font-bold text-lg text-slate-200 mb-6">
            {lang === "en" ? "Guidelines for Vulnerable Groups" : "संवेदनशील समूहों के लिए निर्देश"}
          </h3>
          <div className="space-y-4">
            {vulnerables.map((v, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h4 className="font-heading font-bold text-sm text-slate-200">{v.target}</h4>
                  <p className="text-[10px] text-slate-500 mt-0.5">{v.risk}</p>
                </div>
                <div className="text-left md:text-right font-semibold text-slate-300 text-xs max-w-xs">
                  {v.action}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}

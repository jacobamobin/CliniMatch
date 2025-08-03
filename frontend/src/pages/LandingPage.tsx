import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { 
  FaSearch, FaChartBar, FaMapMarkedAlt, FaRobot, FaHospitalAlt, 
  FaUserMd, FaDatabase, FaCode, FaCloud, FaCogs, FaBrain,
  FaGlobe, FaShieldAlt, FaRocket, FaFlask, FaLanguage, FaFilter,
  FaLeaf, FaReact, FaPython
} from 'react-icons/fa';
import { SiTypescript, SiTailwindcss, SiFlask, SiPostgresql, SiSupabase, SiGooglecloud } from 'react-icons/si';

const LandingPage: React.FC = () => {
  const { user, signIn, loading } = useAuth();
  const navigate = useNavigate();

  // Redirect to dashboard if user is authenticated
  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard');
    }
  }, [user, loading, navigate]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5
      }
    }
  };

  const aiProcessSteps = [
    {
      icon: <FaUserMd className="w-8 h-8" />,
      title: "Profile Analysis",
      description: "Your medical profile (age, conditions, medications, location) is securely analyzed and formatted for optimal matching."
    },
    {
      icon: <FaDatabase className="w-8 h-8" />,
      title: "ClinicalTrials.gov API",
      description: "We query the official ClinicalTrials.gov database with over 400,000 studies using advanced search parameters."
    },
    {
      icon: <FaFilter className="w-8 h-8" />,
      title: "Smart Filtering",
      description: "Trials are filtered by location relevance, status (active/recruiting), and eligibility criteria to remove irrelevant results."
    },
    {
      icon: <FaBrain className="w-8 h-8" />,
      title: "AI Translation",
      description: "Google Gemini AI translates complex medical jargon into plain English, making trial information accessible to everyone."
    },
    {
      icon: <FaShieldAlt className="w-8 h-8" />,
      title: "Secure Caching",
      description: "Results are cached in Supabase for faster subsequent searches while maintaining data privacy and security."
    },
    {
      icon: <FaMapMarkedAlt className="w-8 h-8" />,
      title: "Interactive Results",
      description: "View personalized matches with simplified descriptions, eligibility criteria, and interactive maps showing trial locations."
    }
  ];

  const techStack = {
    frontend: [
      { name: "React", icon: <FaReact className="w-6 h-6" />, description: "Modern UI framework" },
      { name: "TypeScript", icon: <SiTypescript className="w-6 h-6" />, description: "Type-safe development" },
      { name: "Tailwind CSS", icon: <SiTailwindcss className="w-6 h-6" />, description: "Utility-first styling" },
      { name: "Framer Motion", icon: <FaRocket className="w-6 h-6" />, description: "Smooth animations" },
      { name: "React Leaflet", icon: <FaMapMarkedAlt className="w-6 h-6" />, description: "Interactive maps" }
    ],
    backend: [
      { name: "Python", icon: <FaPython className="w-6 h-6" />, description: "Core backend language" },
      { name: "Flask", icon: <SiFlask className="w-6 h-6" />, description: "Web framework" },
      { name: "Marshmallow", icon: <FaShieldAlt className="w-6 h-6" />, description: "Data validation" },
      { name: "Threading", icon: <FaCogs className="w-6 h-6" />, description: "Concurrent processing" }
    ],
    ai: [
      { name: "Google Gemini", icon: <FaBrain className="w-6 h-6" />, description: "AI translation" },
      { name: "Natural Language", icon: <FaLanguage className="w-6 h-6" />, description: "Text processing" },
      { name: "Context Analysis", icon: <FaFlask className="w-6 h-6" />, description: "Medical understanding" }
    ],
    data: [
      { name: "Supabase", icon: <SiSupabase className="w-6 h-6" />, description: "Database & Auth" },
      { name: "PostgreSQL", icon: <SiPostgresql className="w-6 h-6" />, description: "Relational database" },
      { name: "ClinicalTrials.gov", icon: <FaGlobe className="w-6 h-6" />, description: "Official trial data" },
      { name: "OpenStreetMap", icon: <FaMapMarkedAlt className="w-6 h-6" />, description: "Geocoding service" }
    ]
  };

  const apis = [
    {
      name: "ClinicalTrials.gov API",
      description: "Official FDA database containing 400,000+ clinical studies worldwide",
      features: ["Real-time data", "Comprehensive search", "Study details", "Location information"]
    },
    {
      name: "Google Gemini AI API",
      description: "Advanced language model for translating medical terminology",
      features: ["Medical context understanding", "Plain English translation", "Safety guidelines", "Contextual awareness"]
    },
    {
      name: "Supabase API",
      description: "PostgreSQL database with real-time features and authentication",
      features: ["User authentication", "Data caching", "Real-time updates", "Secure storage"]
    },
    {
      name: "OpenStreetMap Nominatim",
      description: "Free geocoding service for converting addresses to coordinates",
      features: ["Global coverage", "Address resolution", "Coordinate mapping", "Location services"]
    }
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Hero Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative py-20 px-4"
      >
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-900 to-slate-900"></div>
        </div>

        <div className="relative max-w-6xl mx-auto text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            className="text-5xl md:text-7xl font-bold text-white mb-6"
          >
            CliniMatch
            <span className="bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
              {" "}AI
            </span>
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="text-xl md:text-2xl text-blue-300 mb-8 max-w-4xl mx-auto"
          >
            Revolutionary AI-powered platform that translates complex medical trials into plain English 
            and matches you with relevant clinical studies based on your unique health profile
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            {user ? (
              <Link to="/dashboard">
                <button className="glass-button text-lg px-8 py-4">
                  Go to Dashboard
                </button>
              </Link>
            ) : (
              <button
                onClick={signIn}
                className="glass-button text-lg px-8 py-4"
              >
                Sign in with Google
              </button>
            )}
            <a href="#how-it-works" className="glass-card-dark text-lg px-8 py-4 text-blue-300 hover:text-white transition-colors">
              See How It Works
            </a>
          </motion.div>
        </div>
      </motion.section>

      {/* How It Works Section */}
      <motion.section
        id="how-it-works"
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-20 px-4 bg-slate-800/30"
      >
        <div className="max-w-7xl mx-auto">
          <motion.div variants={itemVariants} className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              How Our AI Works
            </h2>
            <p className="text-xl text-blue-300 max-w-3xl mx-auto">
              Our advanced AI system processes your medical profile through multiple sophisticated steps 
              to find and translate clinical trials specifically for you
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {aiProcessSteps.map((step, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="glass-card-dark p-6 relative"
              >
                <div className="absolute -top-4 -left-4 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  {index + 1}
                </div>
                <div className="text-blue-400 mb-4">
                  {step.icon}
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  {step.title}
                </h3>
                <p className="text-blue-200 leading-relaxed">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* APIs Used Section */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-20 px-4"
      >
        <div className="max-w-6xl mx-auto">
          <motion.div variants={itemVariants} className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              Powerful APIs & Data Sources
            </h2>
            <p className="text-xl text-blue-300">
              We integrate with industry-leading APIs to provide accurate, real-time medical data
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {apis.map((api, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="glass-card-dark p-6"
              >
                <h3 className="text-xl font-semibold text-white mb-3">
                  {api.name}
                </h3>
                <p className="text-blue-200 mb-4 leading-relaxed">
                  {api.description}
                </p>
                <div className="space-y-2">
                  {api.features.map((feature, featureIndex) => (
                    <div key={featureIndex} className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
                      <span className="text-blue-300 text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Tech Stack Section */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-20 px-4 bg-slate-800/30"
      >
        <div className="max-w-7xl mx-auto">
          <motion.div variants={itemVariants} className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              Technology Stack
            </h2>
            <p className="text-xl text-blue-300">
              Built with modern, scalable technologies for reliability and performance
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Frontend */}
            <motion.div variants={itemVariants} className="glass-card-dark p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FaCode className="text-blue-400" />
                Frontend
              </h3>
              <div className="space-y-3">
                {techStack.frontend.map((tech, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="text-blue-400">
                      {tech.icon}
                    </div>
                    <div>
                      <div className="text-white text-sm font-medium">{tech.name}</div>
                      <div className="text-blue-300 text-xs">{tech.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Backend */}
            <motion.div variants={itemVariants} className="glass-card-dark p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FaCloud className="text-green-400" />
                Backend
              </h3>
              <div className="space-y-3">
                {techStack.backend.map((tech, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="text-green-400">
                      {tech.icon}
                    </div>
                    <div>
                      <div className="text-white text-sm font-medium">{tech.name}</div>
                      <div className="text-green-300 text-xs">{tech.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* AI & ML */}
            <motion.div variants={itemVariants} className="glass-card-dark p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FaBrain className="text-purple-400" />
                AI & ML
              </h3>
              <div className="space-y-3">
                {techStack.ai.map((tech, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="text-purple-400">
                      {tech.icon}
                    </div>
                    <div>
                      <div className="text-white text-sm font-medium">{tech.name}</div>
                      <div className="text-purple-300 text-xs">{tech.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Data & Storage */}
            <motion.div variants={itemVariants} className="glass-card-dark p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FaDatabase className="text-orange-400" />
                Data & Storage
              </h3>
              <div className="space-y-3">
                {techStack.data.map((tech, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="text-orange-400">
                      {tech.icon}
                    </div>
                    <div>
                      <div className="text-white text-sm font-medium">{tech.name}</div>
                      <div className="text-orange-300 text-xs">{tech.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Features Preview */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-20 px-4"
      >
        <div className="max-w-6xl mx-auto">
          <motion.div variants={itemVariants} className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-blue-300">
              Everything you need to find and understand clinical trials
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <motion.div variants={itemVariants} className="glass-card-dark p-6 text-center">
              <FaSearch className="w-12 h-12 text-blue-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-3">Smart Matching</h3>
              <p className="text-blue-200">
                AI analyzes your profile against thousands of trials to find perfect matches
              </p>
            </motion.div>

            <motion.div variants={itemVariants} className="glass-card-dark p-6 text-center">
              <FaLanguage className="w-12 h-12 text-green-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-3">Plain English</h3>
              <p className="text-blue-200">
                Complex medical jargon automatically translated into understandable language
              </p>
            </motion.div>

            <motion.div variants={itemVariants} className="glass-card-dark p-6 text-center">
              <FaMapMarkedAlt className="w-12 h-12 text-purple-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-3">Interactive Maps</h3>
              <p className="text-blue-200">
                Visualize trial locations with real-time geocoding and filtering
              </p>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Stats */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-20 px-4 bg-slate-800/30"
      >
        <div className="max-w-4xl mx-auto">
          <div className="glass-card-dark p-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
              <motion.div variants={itemVariants}>
                <div className="text-4xl font-bold text-blue-400 mb-2">400K+</div>
                <div className="text-blue-300">Clinical Trials</div>
              </motion.div>
              <motion.div variants={itemVariants}>
                <div className="text-4xl font-bold text-green-400 mb-2">AI</div>
                <div className="text-green-300">Translation</div>
              </motion.div>
              <motion.div variants={itemVariants}>
                <div className="text-4xl font-bold text-purple-400 mb-2">Real-time</div>
                <div className="text-purple-300">Data</div>
              </motion.div>
              <motion.div variants={itemVariants}>
                <div className="text-4xl font-bold text-orange-400 mb-2">Secure</div>
                <div className="text-orange-300">Storage</div>
              </motion.div>
            </div>
          </div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="py-20 px-4"
      >
        <div className="max-w-4xl mx-auto text-center">
          <motion.div variants={itemVariants}>
            <h2 className="text-4xl font-bold text-white mb-6">
              Ready to Find Your Clinical Trial?
            </h2>
            <p className="text-xl text-blue-300 mb-8">
              Join thousands of patients using AI to find clinical trials that could change their lives
            </p>
            {!user && (
              <button
                onClick={signIn}
                className="glass-button text-lg px-8 py-4"
              >
                Get Started with Google
              </button>
            )}
          </motion.div>
        </div>
      </motion.section>
    </div>
  );
};

export default LandingPage; 
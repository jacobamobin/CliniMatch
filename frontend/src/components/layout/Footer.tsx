import React from 'react';
import { motion } from 'framer-motion';

const Footer: React.FC = () => {
  return (
    <motion.footer 
      className="glass-dark border-t border-blue-400/20 mt-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div className="text-center md:text-left">
            <h3 className="text-lg font-semibold text-white mb-2">CliniMatch</h3>
            <p className="text-blue-300 text-sm">
              Connecting patients with clinical trials through AI-powered matching.
            </p>
          </div>

          {/* Quick Links */}
          <div className="text-center">
            <h4 className="text-white font-medium mb-3">Quick Links</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/profile" className="text-blue-300 hover:text-white transition-colors">
                  Create Profile
                </a>
              </li>
              <li>
                <a href="/results" className="text-blue-300 hover:text-white transition-colors">
                  View Results
                </a>
              </li>
              <li>
                <a href="/map" className="text-blue-300 hover:text-white transition-colors">
                  Trial Map
                </a>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div className="text-center md:text-right">
            <h4 className="text-white font-medium mb-3">Contact</h4>
            <p className="text-blue-300 text-sm">
              For support or questions about clinical trials
            </p>
            <p className="text-blue-300 text-sm mt-1">
              jacobamobin@gmail.com
            </p>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-blue-400/20 mt-8 pt-6 text-center">
          <p className="text-blue-300 text-sm">
            © 2025 Jacob Mobin. All rights reserved. This tool is for informational purposes only and does not constitute medical advice.
          </p>
        </div>
      </div>
    </motion.footer>
  );
};

export default Footer; 
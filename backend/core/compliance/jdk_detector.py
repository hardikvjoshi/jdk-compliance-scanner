"""
JDK version detector - shared component (DRY principle)
Parses java -version output from different vendors
"""
import re
from typing import Optional, Dict, List


class JDKDetector:
    """Detects JDK version and vendor from java -version output"""
    
    # Vendor patterns
    VENDOR_PATTERNS = {
        "Zulu": [r"Zulu", r"Azul"],
        "Oracle": [r"Oracle", r"Java\(TM\)", r"Java SE"],
        "Amazon": [r"Amazon", r"Corretto"],
        "OpenJDK": [r"OpenJDK", r"openjdk"],
        "Eclipse": [r"Eclipse", r"Temurin"],
        "IBM": [r"IBM", r"J9"],
        "SAP": [r"SAP"],
    }
    
    # Version patterns - match major versions: 8, 11, 17, 18, 19, 21, 22, etc.
    VERSION_PATTERNS = [
        r'"(\d+)',  # "17.0.1"
        r'version "(\d+)',  # version "17"
        r'(\d+)\.(\d+)\.(\d+)',  # 17.0.1
        r'(\d+)\.(\d+)',  # 17.0
        r'jdk-(\d+)',  # jdk-17
        r'1\.(\d+)',  # 1.8 (for Java 8)
    ]
    
    def parse_version_output(self, output: str) -> Optional[Dict[str, str]]:
        """
        Parse java -version output to extract version and vendor
        
        Args:
            output: Combined stdout and stderr from java -version command
            
        Returns:
            Dictionary with 'version' and 'vendor' keys, or None if parsing fails
        """
        if not output:
            return None
        
        # Extract major version
        major_version = self._extract_major_version(output)
        if not major_version:
            return None
        
        # Extract vendor
        vendor = self._extract_vendor(output)
        
        return {
            "version": str(major_version),
            "vendor": vendor or "Unknown",
            "full_output": output
        }
    
    def _extract_major_version(self, output: str) -> Optional[int]:
        """Extract major JDK version from output"""
        # Handle Java 8 special case (version 1.8)
        if re.search(r'1\.8\.', output) or re.search(r'"1\.8', output):
            return 8
        
        # Try all version patterns
        for pattern in self.VERSION_PATTERNS:
            match = re.search(pattern, output)
            if match:
                version_str = match.group(1)
                try:
                    version_int = int(version_str)
                    # Java 8 appears as 1.8, so if we see 1.x, it's Java 8
                    if version_int == 1 and len(match.groups()) > 1:
                        minor = int(match.group(2))
                        if minor == 8:
                            return 8
                    # Otherwise return the major version
                    if version_int >= 8:  # Valid JDK versions
                        return version_int
                except ValueError:
                    continue
        
        return None
    
    def _extract_vendor(self, output: str) -> Optional[str]:
        """Extract vendor name from output"""
        output_lower = output.lower()
        
        for vendor, patterns in self.VENDOR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    return vendor
        
        return "Unknown"
    
    def get_fallback_commands(self) -> List[str]:
        """
        Get list of fallback commands to confirm Java absence
        Shared logic for all scanners (DRY)
        """
        return [
            "which java",
            "whereis java",
            "command -v java",
            "/usr/bin/java -version",
            "/usr/local/bin/java -version",
        ]


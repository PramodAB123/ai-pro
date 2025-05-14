import streamlit as st
import PyPDF2
import io
import os
import re
import requests
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv
from urllib.parse import urlparse
import random

# Set page config with dark theme
st.set_page_config(
    page_title="AI Resume Customizer",
    layout="wide",
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Dark theme CSS with appropriate text colors
st.markdown("""
<style>
    /* Dark theme color scheme */
    :root {
        --primary-color: #6C63FF;
        --secondary-color: #8E85FF;
        --accent-color: #4A42D1;
        --background-color: #121212;
        --card-bg: #1E1E1E;
        --text-color: #E0E0E0;
        --text-muted: #A0A0A0;
        --border-color: #333333;
    }

    /* Main container styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    /* Header styling */
    .header {
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        padding: 3rem 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    .header h1 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }

    .header p {
        font-size: 1.2rem;
        opacity: 0.9;
    }

    /* Card styling */
    .card {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        border: 1px solid var(--border-color);
        color: var(--text-color);
        transition: transform 0.2s ease;
    }

    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }

    /* Text elements */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color) !important;
    }

    p, div {
        color: var(--text-color) !important;
    }

    /* Button styling */
    .stButton>button {
        background: var(--primary-color);
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        border: none;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background: var(--secondary-color);
        transform: translateY(-1px);
        color: white !important;
    }

    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed var(--accent-color);
        border-radius: 0.5rem;
        padding: 1rem;
        background: var(--card-bg) !important;
    }

    /* Progress bar styling */
    .progress-bar {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 1rem;
        height: 0.5rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--card-bg) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    .sidebar-header {
        padding: 1rem;
        border-bottom: 1px solid var(--border-color);
    }

    /* Input fields */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea {
        background: var(--card-bg) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Radio buttons */
    .stRadio>div {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 0.5rem;
        padding: 0.5rem;
    }

    /* Select slider */
    .stSelectSlider>div {
        background: var(--card-bg) !important;
    }

    /* Checkbox */
    .stCheckbox>label {
        color: var(--text-color) !important;
    }

    /* Animation classes */
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .header {
            padding: 2rem 1rem;
        }
        
        .header h1 {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def clean_html(raw_html):
    """Remove HTML tags from a string"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def get_company_info(url):
    """Scrape company website for basic information"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic company info
        company_name = soup.find('title').get_text() if soup.find('title') else urlparse(url).netloc
        description = soup.find('meta', attrs={'name': 'description'})
        description = description['content'] if description else "No description found"
        
        # Try to find about page
        about_link = None
        for link in soup.find_all('a', href=True):
            if 'about' in link['href'].lower():
                about_link = link['href'] if link['href'].startswith('http') else f"{url.rstrip('/')}/{link['href'].lstrip('/')}"
                break
        
        # Get more details from about page if available
        about_text = ""
        if about_link:
            try:
                about_response = requests.get(about_link, headers=headers, timeout=10)
                about_soup = BeautifulSoup(about_response.text, 'html.parser')
                about_text = about_soup.get_text()[:1000]  # Limit text length
            except:
                about_text = ""
        
        # Try to find careers/jobs page for company culture insights
        careers_link = None
        for link in soup.find_all('a', href=True):
            if any(keyword in link['href'].lower() for keyword in ['career', 'job', 'work']):
                careers_link = link['href'] if link['href'].startswith('http') else f"{url.rstrip('/')}/{link['href'].lstrip('/')}"
                break
        
        # Get culture info from careers page if available
        culture_text = ""
        if careers_link:
            try:
                careers_response = requests.get(careers_link, headers=headers, timeout=10)
                careers_soup = BeautifulSoup(careers_response.text, 'html.parser')
                culture_text = careers_soup.get_text()[:800]  # Limit text length
            except:
                culture_text = ""
        
        # Try to extract company size, industry, and location
        company_size = "Mid-sized (100-500 employees)"
        industry = "Technology & Software Development"
        location = "Multiple locations worldwide"
        
        # Look for LinkedIn link to get more info
        linkedin_link = None
        for link in soup.find_all('a', href=True):
            if 'linkedin.com/company' in link['href'].lower():
                linkedin_link = link['href']
                break
        
        if linkedin_link:
            try:
                linkedin_response = requests.get(linkedin_link, headers=headers, timeout=10)
                linkedin_soup = BeautifulSoup(linkedin_response.text, 'html.parser')
                
                # Try to extract company details from LinkedIn
                company_details = linkedin_soup.find_all('dd', class_='org-page-details__definition-text')
                if len(company_details) >= 3:
                    company_size = company_details[0].get_text().strip()
                    industry = company_details[1].get_text().strip()
                    location = company_details[2].get_text().strip()
            except:
                pass
        
        # Extract all text from the main page for analysis
        main_text = soup.get_text()[:5000]
        
        return {
            "name": clean_html(company_name),
            "description": clean_html(description),
            "about_raw": clean_html(about_text),
            "culture_raw": clean_html(culture_text),
            "main_text": clean_html(main_text),
            "size": company_size,
            "industry": industry,
            "location": location,
            "website": url
        }
    except Exception as e:
        st.error(f"Error scraping company website: {str(e)}")
        # Return default values if scraping fails
        domain = urlparse(url).netloc
        company_name = domain.split('.')[0].title()
        return {
            "name": company_name,
            "description": "",
            "about_raw": "",
            "culture_raw": "",
            "main_text": "",
            "size": "Mid-sized (100-500 employees)",
            "industry": "Technology & Software Development",
            "location": "Multiple locations worldwide",
            "website": url
        }

# Initialize Groq client
try:
    api_key = os.environ.get("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")
    if not api_key:
        st.warning("Please set your GROQ_API_KEY in the .env file or enter it below")
        api_key = st.text_input("Enter your Groq API key:", type="password")
        client = Groq(api_key=api_key)
        if not api_key:
            st.stop()
    

except Exception as e:
    st.error(f"Failed to initialize Groq client: {str(e)}")
    st.stop()

def extract_text_from_pdf(uploaded_file):
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        return "\n".join(page.extract_text() for page in pdf_reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def extract_match_score(analysis_text):
    """Extract the match score percentage from the analysis text."""
    # First try the specific format we requested
    specific_match = re.search(r'## Match Score:\s*(\d+)%', analysis_text)
    if specific_match:
        return int(specific_match.group(1))
    
    # Fallback to more general pattern
    general_match = re.search(r'Match Score.*?(\d+)%', analysis_text)
    if general_match:
        return int(general_match.group(1))
    
    return 0

def analyze_company_info(company_info):
    """Generate detailed company insights using AI analysis."""
    # Prepare the context from scraped information
    company_context = f"""
    Company Name: {company_info['name']}
    Website: {company_info['website']}
    Industry: {company_info['industry']}
    Size: {company_info['size']}
    Location: {company_info['location']}
    
    Raw Description: {company_info['description']}
    
    Raw About Text: {company_info['about_raw']}
    
    Raw Culture Text: {company_info['culture_raw']}
    
    Additional Website Text: {company_info['main_text']}
    """
    
    prompt = f"""
    Based on the following information about a company, generate a comprehensive analysis of the company.
    
    {company_context}
    
    Please provide the following sections:
    
    1. Company Overview: A detailed description of what the company does, its market position, and its core business. (3-4 sentences)
    
    2. Mission and Values: What appears to be the company's mission, vision, and core values based on the available information. (3-4 bullet points)
    
    3. Company Culture: Insights about the company's work environment, team dynamics, and organizational culture. (3-4 bullet points)
    
    4. Work Environment: What it might be like to work at this company, including benefits, work-life balance, and growth opportunities. (3-4 bullet points)
    
    5. Industry Position: The company's standing in its industry, competitors, and market differentiation. (2-3 sentences)
    
    Format each section with a clear header (##) and use bullet points where appropriate. Make the content detailed but concise.
    If information is limited, make reasonable inferences based on the company's industry, size, and other available details.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=0.4,
            max_tokens=2000,
            stream=False
        )
        return clean_html(response.choices[0].message.content)
    except Exception as e:
        # Fallback content if API fails
        return f"""
        ## Company Overview
        {company_info['name']} is a {company_info['industry']} company that provides innovative solutions to meet client needs. With a focus on quality and customer satisfaction, they have established themselves as a reliable partner in their industry. The company operates from {company_info['location']} and serves clients across various sectors.
        
        ## Mission and Values
        • Delivering high-quality solutions that exceed client expectations
        • Fostering innovation and continuous improvement
        • Building long-term relationships with clients and partners
        • Maintaining ethical business practices and integrity in all operations
        
        ## Company Culture
        • Collaborative environment that encourages teamwork and knowledge sharing
        • Results-oriented approach with a focus on achieving measurable outcomes
        • Emphasis on professional development and continuous learning
        • Open communication and transparency across all levels of the organization
        
        ## Work Environment
        • Flexible work arrangements that support work-life balance
        • Competitive compensation and benefits package
        • Opportunities for career advancement and skill development
        • Inclusive workplace that values diversity and different perspectives
        
        ## Industry Position
        {company_info['name']} has established itself as a competitive player in the {company_info['industry']} sector. By focusing on innovation and customer-centric solutions, they differentiate themselves from competitors and continue to expand their market presence.
        """

def analyze_resume_with_groq(jd_text, resume_text, company_info=None):
    """Send JD and resume to Groq API for analysis."""
    company_context = ""
    if company_info:
        company_context = f"""
        Company Context:
        - Name: {company_info['name']}
        - Industry: {company_info['industry']}
        - Size: {company_info['size']}
        - Location: {company_info['location']}
        """
    
    prompt = f"""
    Analyze this job description and resume pair. First, calculate and provide a Match Score between 0-100% 
    based on how well the resume matches the job requirements. Then provide specific, actionable suggestions.
    
    {company_context}

    Job Description:
    {jd_text[:7000]}

    Resume:
    {resume_text[:7000]}

    Provide your analysis with these sections:
    1. Match Score (0-100%) with justification - format exactly as: '## Match Score: X%' where X is the score
    2. Company-Specific Recommendations (considering company culture and values)
    3. Top 3 Missing Keywords
    4. Top 3 Overused Terms
    5. Skills Gap Analysis
    6. Specific Content Improvements
    7. Suggested Action Items
    8. Salary Considerations (what aspects of the resume might impact salary negotiation)

    Format with clear section headers (##) and bullet points. Do not include any HTML tags in your response.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=0.3,
            max_tokens=4000,
            stream=False
        )
        return clean_html(response.choices[0].message.content)
    except Exception as e:
        return f"API Error: {str(e)}"

def create_placement_indicator(score):
    """Create a visual indicator for placement probability."""
    st.subheader("Resume Match Score")
    
    if score >= 80:
        color = "#10B981"  # Green
        emoji = "🎯"
        message = "Excellent match! High probability of getting placed"
        icon = "✨"
    elif score >= 60:
        color = "#84CC16"  # Light Green
        emoji = "👍"
        message = "Good match - some optimizations could make it perfect"
        icon = "🔍"
    elif score >= 40:
        color = "#F59E0B"  # Amber
        emoji = "⚠️"
        message = "Moderate match - needs improvements"
        icon = "📝"
    elif score >= 20:
        color = "#F97316"  # Orange
        emoji = "🤔"
        message = "Below average - significant improvements needed"
        icon = "🛠️"
    else:
        color = "#EF4444"  # Red
        emoji = "❌"
        message = "Poor match - major overhaul required"
        icon = "🚨"
    
    st.markdown(
        f"""
        <div class="card">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                <span style="font-size: 24px;">{emoji}</span>
                <h2 style="margin: 0;">Match Score: {score}%</h2>
                <span style="font-size: 24px;">{icon}</span>
            </div>
            <p style="margin-bottom: 15px;">{message}</p>
            <div style="width: 100%; background: #333; border-radius: 10px;">
                <div style="width: {score}%; background: {color}; height: 10px; border-radius: 10px; 
                    display: flex; align-items: center; justify-content: flex-end; padding-right: 5px;">
                    <span style="color: white; font-size: 10px;">{score}%</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def format_analysis_content(analysis_text):
    """Format the analysis content into styled boxes."""
    # First remove any HTML tags that might have slipped through
    clean_text = clean_html(analysis_text)
    
    # Split into sections
    sections = re.split(r'\n## ', clean_text)
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        if '\n' in section:
            title, content = section.split('\n', 1)
        else:
            title = section
            content = ""
        
        # Skip the Match Score section since we display it separately
        if "Match Score" in title:
            continue
            
        # Different card styles for different sections
        if "Recommendations" in title:
            icon = "💡"
            border_color = "#6C63FF"
        elif "Missing" in title:
            icon = "🔎"
            border_color = "#4CAF50"
        elif "Overused" in title:
            icon = "🔄"
            border_color = "#FF9800"
        elif "Gap" in title:
            icon = "📉"
            border_color = "#2196F3"
        elif "Improvements" in title:
            icon = "🛠️"
            border_color = "#9C27B0"
        elif "Action" in title:
            icon = "✅"
            border_color = "#00BCD4"
        else:
            icon = "📌"
            border_color = "#607D8B"
        
        st.markdown(
            f"""
            <div class="card" style="border-left: 4px solid {border_color};">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <span style="font-size: 24px;">{icon}</span>
                    <h3 style="margin: 0;">{title}</h3>
                </div>
                <div style="color: var(--text-color);">
                    {content.replace('\n', '<br>')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def estimate_salary_range(jd_text, resume_text, company_info=None):
    """Estimate salary range based on job description, resume, and company info."""
    company_context = ""
    if company_info:
        company_context = f"""
        Company Context:
        - Name: {company_info['name']}
        - Industry: {company_info['industry']}
        - Size: {company_info['size']}
        - Location: {company_info['location']}
        """
    
    prompt = f"""
    Analyze this job description and resume to provide salary insights.
    
    {company_context}

    Job Description:
    {jd_text[:5000]}

    Resume:
    {resume_text[:5000]}

    Based on the job description, resume, and company information, provide:
    1. Estimated salary range for this position
    2. Factors that might affect the salary (experience level, skills, location, etc.)
    3. Industry average for similar positions
    4. Negotiation tips based on the candidate's profile
    
    Format with clear section headers (##) and bullet points. Be specific about currency and ranges.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=0.3,
            max_tokens=2000,
            stream=False
        )
        return clean_html(response.choices[0].message.content)
    except Exception as e:
        return f"Salary Estimation Error: {str(e)}"

def display_company_insights(company_analysis):
    """Display AI-generated company insights in styled cards."""
    if not company_analysis:
        return
    
    st.markdown("""
    <div class="card fade-in">
        <h2>🏢 Company Insights</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Split into sections
    sections = re.split(r'\n## ', company_analysis)
    
    # Define icons and colors for each section
    section_styles = {
        "Company Overview": {"icon": "🏢", "color": "#6C63FF"},
        "Mission and Values": {"icon": "🚀", "color": "#4CAF50"},
        "Company Culture": {"icon": "🌟", "color": "#FF9800"},
        "Work Environment": {"icon": "🏡", "color": "#2196F3"},
        "Industry Position": {"icon": "📊", "color": "#9C27B0"}
    }
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        if '\n' in section:
            title, content = section.split('\n', 1)
        else:
            title = section
            content = ""
        
        # Get icon and color for this section
        style = section_styles.get(title, {"icon": "📌", "color": "#607D8B"})
        
        # Clean up asterisks and convert to proper bullet points
        content = re.sub(r'\*\s*([^*\n]+)', r'• \1', content)
        
        st.markdown(
            f"""
            <div class="card" style="border-left: 4px solid {style['color']};">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <span style="font-size: 24px;">{style['icon']}</span>
                    <h3 style="margin: 0;">{title}</h3>
                </div>
                <div style="color: var(--text-color);">
                    {content.replace('\n', '<br>')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def display_salary_insights(salary_text):
    """Display salary insights in a styled card."""
    if not salary_text:
        return
    
    st.markdown("""
    <div class="card fade-in">
        <h2>💰 Salary Insights</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Split into sections
    sections = re.split(r'\n## ', salary_text)
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        if '\n' in section:
            title, content = section.split('\n', 1)
        else:
            title = section
            content = ""
        
        # Different card styles for different sections
        if "Estimated" in title or "Range" in title:
            icon = "💰"
            border_color = "#4CAF50"  # Green
        elif "Factors" in title:
            icon = "📊"
            border_color = "#2196F3"  # Blue
        elif "Average" in title or "Industry" in title:
            icon = "📈"
            border_color = "#9C27B0"  # Purple
        elif "Negotiation" in title or "Tips" in title:
            icon = "🤝"
            border_color = "#FF9800"  # Orange
        else:
            icon = "💵"
            border_color = "#607D8B"  # Gray
        
        # Clean up asterisks and convert to proper bullet points
        content = re.sub(r'\*\s*\*\*([^*]+)\*\*\s*:', r'• <strong>\1</strong>:', content)
        content = re.sub(r'\*\s*\*\*([^*]+)\*\*', r'• <strong>\1</strong>', content)
        content = re.sub(r'\*\s*\*([^*]+)\*\s*:', r'• <strong>\1</strong>:', content)
        content = re.sub(r'\*\s*\*([^*]+)\*', r'• <strong>\1</strong>', content)
        content = re.sub(r'\*\s*([^*\n]+)', r'• \1', content)
        
        st.markdown(
            f"""
            <div class="card" style="border-left: 4px solid {border_color};">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <span style="font-size: 24px;">{icon}</span>
                    <h3 style="margin: 0;">{title}</h3>
                </div>
                <div style="color: var(--text-color);">
                    {content.replace('\n', '<br>')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def main():
    # Header section
    st.markdown("""
    <div class="header fade-in">
        <h1>🎯 AI Resume Analyzer</h1>
        <p>Optimize your resume for your dream job with AI-powered insights</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <h2>How It Works</h2>
        </div>
        """, unsafe_allow_html=True)
        
        steps = [
            ("1", "Upload Resume", "Upload your current resume in PDF format"),
            ("2", "Add Job Description", "Paste or upload the job description you're targeting"),
            ("3", "Add Company URL", "Provide the company website for deeper insights"),
            ("4", "Get Insights", "Receive AI-powered optimization suggestions and salary insights")
        ]
        
        for num, title, desc in steps:
            st.markdown(f"""
            <div class="card fade-in">
                <h3>Step {num}: {title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Resume upload section
        st.markdown("""
        <div class="card fade-in">
            <h2>📄 Upload Your Resume</h2>
        </div>
        """, unsafe_allow_html=True)
        
        resume_file = st.file_uploader("Choose your resume (PDF)", type="pdf", key="resume")

        # Job description section
        st.markdown("""
        <div class="card fade-in">
            <h2>🎯 Job Description</h2>
        </div>
        """, unsafe_allow_html=True)
        
        jd_option = st.radio("Choose input method:", ["Upload PDF", "Paste Text"])
        
        if jd_option == "Upload PDF":
            jd_file = st.file_uploader("Upload job description (PDF)", type="pdf", key="jd")
        else:
            jd_text = st.text_area("Paste job description here", height=200)

    with col2:
        # Additional options
        st.markdown("""
        <div class="card fade-in">
            <h2>⚙️ Options</h2>
        </div>
        """, unsafe_allow_html=True)
        
        analysis_depth = st.select_slider(
            "Analysis Depth",
            options=["Basic", "Standard", "Detailed"],
            value="Standard"
        )
        
        include_keywords = st.checkbox("Include keyword analysis", value=True)
        include_skills = st.checkbox("Include skills gap analysis", value=True)
        include_formatting = st.checkbox("Include formatting suggestions", value=True)
        include_salary = st.checkbox("Include salary insights", value=True)

        # Company website input
        st.markdown("""
        <div class="card fade-in">
            <h2>🏢 Company Info</h2>
        </div>
        """, unsafe_allow_html=True)
        company_url = st.text_input("Company website URL (for better customization)")

    # Analysis button
    if st.button("🚀 Analyze Resume", use_container_width=True):
        if not resume_file:
            st.error("Please upload your resume first")
            return
            
        if jd_option == "Upload PDF" and not jd_file:
            st.error("Please upload or paste the job description")
            return
        elif jd_option == "Paste Text" and not jd_text:
            st.error("Please paste the job description")
            return
            
        with st.spinner("Analyzing your resume..."):
            # Extract text from files
            resume_text = extract_text_from_pdf(resume_file)
            if not resume_text:
                return
                
            if jd_option == "Upload PDF":
                jd_text = extract_text_from_pdf(jd_file)
                if not jd_text:
                    return
            
            # Get company info if URL provided
            company_info = None
            company_analysis = None
            if company_url:
                with st.spinner("Gathering company information..."):
                    company_info = get_company_info(company_url)
                    with st.spinner("Analyzing company profile..."):
                        company_analysis = analyze_company_info(company_info)
            
            # Perform analysis
            analysis_text = analyze_resume_with_groq(jd_text, resume_text, company_info)
            
            # Get salary insights if requested
            salary_text = None
            if include_salary:
                with st.spinner("Generating salary insights..."):
                    salary_text = estimate_salary_range(jd_text, resume_text, company_info)
            
            # Display results
            st.success("Analysis complete!")
            
            # Display company info if available
            if company_info and company_analysis:
                display_company_insights(company_analysis)
            
            with st.expander("Resume Analysis Results", expanded=True):
                # Extract and display match score
                match_score = extract_match_score(analysis_text)
                create_placement_indicator(match_score)
                
                # Display the rest of the analysis
                format_analysis_content(analysis_text)
            
            # Display salary insights if available
            if salary_text:
                with st.expander("Salary Insights", expanded=True):
                    display_salary_insights(salary_text)

if __name__ == "__main__":
    main()

import pdfplumber
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk
import os

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class PDFProcessor:
    def __init__(self):
        self.summarizers = {
            'lsa': LsaSummarizer(),
            'lexrank': LexRankSummarizer(),
            'textrank': TextRankSummarizer()
        }
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text content from a PDF file."""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Clean up the text
            text = self._clean_text(text)
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def _clean_text(self, text):
        """Clean and normalize extracted text."""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\@\#\$\%\&\*\+\=\<\>\~\`\|\\]', '', text)
        
        return text.strip()
    
    def generate_summary(self, text, sentences_count=3, method='lsa'):
        """Generate a summary of the given text."""
        if not text or len(text.strip()) < 100:
            return "Text too short to summarize."
        
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summarizer = self.summarizers.get(method, self.summarizers['lsa'])
            
            # Generate summary
            summary_sentences = summarizer(parser.document, sentences_count)
            summary = ' '.join([str(sentence) for sentence in summary_sentences])
            
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Unable to generate summary."
    
    def extract_key_messages(self, text, max_messages=5):
        """Extract key messages or important points from the text."""
        if not text or len(text.strip()) < 100:
            return []
        
        try:
            # Split text into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            # Simple heuristic: look for sentences with certain keywords that might indicate importance
            important_keywords = [
                'important', 'key', 'main', 'primary', 'essential', 'critical',
                'significant', 'major', 'conclusion', 'result', 'finding',
                'recommendation', 'summary', 'overview', 'objective', 'goal'
            ]
            
            scored_sentences = []
            for sentence in sentences:
                score = 0
                sentence_lower = sentence.lower()
                
                # Score based on keywords
                for keyword in important_keywords:
                    if keyword in sentence_lower:
                        score += 1
                
                # Score based on sentence position (first and last sentences often important)
                if sentences.index(sentence) < 3 or sentences.index(sentence) >= len(sentences) - 3:
                    score += 1
                
                # Score based on sentence length (medium length sentences often more informative)
                if 50 <= len(sentence) <= 200:
                    score += 1
                
                scored_sentences.append((sentence, score))
            
            # Sort by score and return top messages
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            key_messages = [sentence for sentence, score in scored_sentences[:max_messages] if score > 0]
            
            return key_messages
        except Exception as e:
            print(f"Error extracting key messages: {e}")
            return []
    
    def get_document_title(self, text, filename):
        """Extract or generate a title for the document."""
        try:
            # Try to find a title in the first few lines
            lines = text.split('\n')[:10]
            
            for line in lines:
                line = line.strip()
                # Look for lines that might be titles (short, capitalized, etc.)
                if 10 <= len(line) <= 100 and line.count(' ') <= 10:
                    # Check if it looks like a title
                    words = line.split()
                    if len(words) >= 2 and sum(1 for word in words if word[0].isupper()) >= len(words) * 0.5:
                        return line
            
            # If no title found, use filename without extension
            title = os.path.splitext(filename)[0]
            title = re.sub(r'[_-]', ' ', title)
            return title.title()
        except Exception as e:
            print(f"Error extracting title: {e}")
            return filename
    
    def process_pdf(self, pdf_path, filename):
        """Complete PDF processing: extract text, generate summary, and extract key messages."""
        try:
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text:
                return {
                    'title': filename,
                    'text': '',
                    'summary': 'Unable to extract text from PDF.',
                    'key_messages': []
                }
            
            # Generate title
            title = self.get_document_title(text, filename)
            
            # Generate summary
            summary = self.generate_summary(text, sentences_count=3)
            
            # Extract key messages
            key_messages = self.extract_key_messages(text, max_messages=5)
            
            return {
                'title': title,
                'text': text,
                'summary': summary,
                'key_messages': key_messages
            }
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return {
                'title': filename,
                'text': '',
                'summary': f'Error processing PDF: {str(e)}',
                'key_messages': []
            }


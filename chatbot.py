import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time
import xml.etree.ElementTree as ET
import re
from urllib.parse import urlparse
from openai import OpenAI

load_dotenv()

class PapuyChatbot:
    def __init__(self):
        self.messages = [
            {
                "role": "system",
                "content": """Eres un asistente médico llamado Papuy, diseñado para ayudar a Emily en su investigación médica. 
                
                Para consultas médicas:
                - Responde en español de manera profesional y académica
                - Cita artículos en formato APA 7ma edición
                - Incluye DOI o URL de los artículos citados
                - Estructura las referencias al final de cada respuesta
                - Mantén un tono profesional y basado en evidencia
                
                Para consultas no médicas:
                - Mantén un tono amigable y personal, llamando a la usuaria "Emily"
                - Responde como un asistente conversacional normal
                - Puedes ser más casual y empático
                - No es necesario incluir citas o referencias
                - Puedes usar emojis y un lenguaje más relajado
                
                En todos los casos:
                - Sé empático y atento
                - Mantén un tono respetuoso
                - Si no estás seguro de algo, admítelo honestamente
                - Prioriza la seguridad y el bienestar de Emily"""
            }
        ]
        self.openai = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Update system message to include APA citation requirements
        self.system_message = """Eres Papuy, un asistente de investigación médica muy útil. Ayudas a estudiantes de medicina a encontrar y entender artículos médicos. 
        
        Reglas importantes:
        1. Responde siempre en español.
        2. Al citar artículos, usa SIEMPRE el formato APA 7ma edición.
        3. Cuando menciones información de un artículo, incluye una cita en el texto (Autor et al., Año).
        4. Al final de cada respuesta que incluya referencias, agrega una sección "Referencias" con el listado completo en formato APA.
        5. Para artículos en inglés, mantén el título original en inglés en la referencia.
        6. Estructura las referencias así:
           - Artículos: Apellido, N., & Apellido, N. (Año). Título del artículo. Nombre de la revista, Volumen(Número), páginas. DOI
           - Si no hay DOI, usa el URL cuando esté disponible
        7. Ordena las referencias alfabéticamente.
        8. Cuando resumas artículos, incluye:
           - Objetivo del estudio
           - Metodología
           - Resultados principales
           - Conclusiones
           - Limitaciones (si las hay)
        """
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        self.chain = (
            {
                "input": RunnablePassthrough(),
                "chat_history": lambda x: self.messages
            }
            | self.prompt
            | self.openai
            | StrOutputParser()
        )
        self.pubmed_api_key = os.getenv("PUBMED_API_KEY")
        self.serp_api_key = os.getenv("SERP_API_KEY")
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.serp_url = "https://serpapi.com/search.json"
        
    def translate_text(self, text):
        try:
            prompt = f"Traduce el siguiente texto al español, manteniendo el formato y la estructura:\n\n{text}"
            response = self.chain.invoke(prompt)
            return response
        except Exception as e:
            return f"Error en la traducción: {str(e)}"
        
    def search_google_scholar(self, query, language="en"):
        try:
            params = {
                "engine": "google_scholar",
                "q": query,
                "api_key": self.serp_api_key,
                "num": 3,
                "hl": language  # Set language parameter
            }
            
            response = requests.get(self.serp_url, params=params)
            data = response.json()
            
            if "error" in data:
                return f"Error en la búsqueda de Google Scholar: {data['error']}"
            
            papers = []
            for result in data.get("organic_results", []):
                paper = {
                    'title': result.get('title', 'Sin título'),
                    'title_es': self.translate_text(result.get('title', 'Sin título')) if language == "en" else result.get('title', 'Sin título'),
                    'authors': [author.get('name', '') for author in result.get('publication_info', {}).get('authors', [])],
                    'year': result.get('publication_info', {}).get('summary', '').split('-')[-1].strip() if result.get('publication_info', {}).get('summary') else 'Sin año',
                    'url': result.get('link', 'URL no disponible'),
                    'abstract': result.get('snippet', 'Resumen no disponible'),
                    'abstract_es': self.translate_text(result.get('snippet', 'Resumen no disponible')) if language == "en" else result.get('snippet', 'Resumen no disponible'),
                    'source': 'Google Scholar',
                    'cited_by': result.get('inline_links', {}).get('cited_by', {}).get('total', 0),
                    'pdf_link': next((resource.get('link') for resource in result.get('resources', []) 
                                   if resource.get('file_format') == 'PDF'), None)
                }
                papers.append(paper)
            
            return papers
        except Exception as e:
            return f"Error al buscar en Google Scholar: {str(e)}"
    
    def search_pubmed(self, query, language="en"):
        try:
            # First, search for articles
            search_url = f"{self.base_url}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": "3"
            }
            if self.pubmed_api_key:
                params["api_key"] = self.pubmed_api_key
                
            response = requests.get(search_url, params=params)
            search_data = response.json()
            
            if "esearchresult" not in search_data or "idlist" not in search_data["esearchresult"]:
                return []
            
            # Get article details
            ids = ",".join(search_data["esearchresult"]["idlist"])
            fetch_url = f"{self.base_url}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": ids,
                "retmode": "xml"
            }
            if self.pubmed_api_key:
                params["api_key"] = self.pubmed_api_key
                
            response = requests.get(fetch_url, params=params)
            root = ET.fromstring(response.content)
            
            papers = []
            for article in root.findall(".//PubmedArticle"):
                title = article.find(".//ArticleTitle")
                authors = article.findall(".//Author")
                year = article.find(".//PubDate/Year")
                abstract = article.find(".//Abstract/AbstractText")
                
                title_text = title.text if title is not None else 'Sin título'
                abstract_text = abstract.text if abstract is not None else 'Resumen no disponible'
                
                paper = {
                    'title': title_text,
                    'title_es': self.translate_text(title_text) if language == "en" else title_text,
                    'authors': [f"{author.find('LastName').text}, {author.find('ForeName').text}" 
                              for author in authors if author.find('LastName') is not None and author.find('ForeName') is not None],
                    'year': year.text if year is not None else 'Sin año',
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{article.find('.//PMID').text}/",
                    'abstract': abstract_text,
                    'abstract_es': self.translate_text(abstract_text) if language == "en" else abstract_text,
                    'source': 'PubMed'
                }
                papers.append(paper)
            
            return papers
        except Exception as e:
            return f"Error al buscar en PubMed: {str(e)}"
    
    def search_papers(self, query, language="en"):
        try:
            # Search both Google Scholar and PubMed
            scholar_papers = self.search_google_scholar(query, language)
            if isinstance(scholar_papers, str):  # Error occurred
                scholar_papers = []
            
            pubmed_papers = self.search_pubmed(query, language)
            if isinstance(pubmed_papers, str):  # Error occurred
                pubmed_papers = []
            
            return scholar_papers + pubmed_papers
        except Exception as e:
            return f"Error al buscar artículos: {str(e)}"
    
    def get_download_link(self, paper_url):
        try:
            if "pubmed.ncbi.nlm.nih.gov" in paper_url:
                return "Para descargar el artículo completo de PubMed, por favor visita el enlace y busca el botón 'Full Text Links' o 'PDF' en la página del artículo."
            
            # Check if we already have a PDF link from SerpAPI
            for paper in self.messages[-2].content.split('\n\n'):
                if paper_url in paper and 'PDF' in paper:
                    return paper.split('PDF: ')[-1].strip()
            
            response = requests.get(paper_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            pdf_link = soup.find('a', {'class': 'pdf-link'})
            if pdf_link:
                return pdf_link['href']
            return "No se encontró un enlace de descarga directo. Por favor, visita el sitio web del artículo."
        except Exception as e:
            return f"Error al obtener el enlace de descarga: {str(e)}"
    
    def analyze_papers(self, papers):
        try:
            analysis_prompt = "Analiza los siguientes artículos y recomienda el mejor basado en su contenido y relevancia:\n\n"
            for i, paper in enumerate(papers, 1):
                analysis_prompt += f"Artículo {i}:\n"
                analysis_prompt += f"Título (Original): {paper['title']}\n"
                analysis_prompt += f"Título (Español): {paper['title_es']}\n"
                analysis_prompt += f"Autores: {', '.join(paper['authors'])}\n"
                analysis_prompt += f"Año: {paper['year']}\n"
                analysis_prompt += f"Fuente: {paper.get('source', 'Desconocida')}\n"
                if paper.get('cited_by'):
                    analysis_prompt += f"Citado por: {paper['cited_by']} veces\n"
                analysis_prompt += f"Resumen (Original): {paper['abstract']}\n"
                analysis_prompt += f"Resumen (Español): {paper['abstract_es']}\n\n"
            
            analysis_prompt += "\nPor favor, proporciona un análisis detallado y recomienda el mejor artículo, explicando por qué es el más relevante."
            
            response = self.chain.invoke(analysis_prompt)
            return response
        except Exception as e:
            return f"Error al analizar los artículos: {str(e)}"
    
    def fetch_full_text(self, url):
        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract main content based on common article containers
            main_content = None
            for container in ['article', 'main', 'div[class*="content"]', 'div[class*="article"]']:
                content = soup.select_one(container)
                if content:
                    main_content = content.get_text()
                    break
            
            if main_content:
                return main_content
            return text
            
        except Exception as e:
            return f"Error al obtener el texto completo: {str(e)}"
    
    def extract_article_sections(self, text):
        try:
            # Common section headers in medical papers
            sections = {
                'introducción': [],
                'métodos': [],
                'resultados': [],
                'discusión': [],
                'conclusión': []
            }
            
            # Split text into paragraphs
            paragraphs = text.split('\n\n')
            current_section = None
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                    
                # Check if paragraph is a section header
                lower_para = para.lower()
                for section in sections.keys():
                    if section in lower_para and len(para) < 100:  # Likely a header
                        current_section = section
                        break
                
                if current_section and current_section in sections:
                    sections[current_section].append(para)
            
            return sections
        except Exception as e:
            return f"Error al extraer secciones: {str(e)}"
    
    def summarize_paper(self, paper_text, url=None):
        try:
            # If URL is provided, try to fetch full text
            full_text = None
            if url:
                full_text = self.fetch_full_text(url)
            
            # Extract sections if we have full text
            sections = None
            if full_text:
                sections = self.extract_article_sections(full_text)
            
            # Create a comprehensive prompt for summarization
            prompt = "Por favor, proporciona un resumen detallado de este artículo médico:\n\n"
            
            if sections:
                prompt += "Secciones del artículo:\n"
                for section, content in sections.items():
                    if content:
                        prompt += f"\n{section.upper()}:\n"
                        prompt += "\n".join(content[:3])  # Include first 3 paragraphs of each section
                        if len(content) > 3:
                            prompt += "\n..."
            else:
                prompt += paper_text
            
            prompt += "\n\nPor favor, proporciona:\n"
            prompt += "1. Un resumen general del artículo\n"
            prompt += "2. Los puntos clave de cada sección\n"
            prompt += "3. Las conclusiones principales\n"
            prompt += "4. La relevancia clínica del estudio"
            
            response = self.chain.invoke(prompt)
            self.messages.append(HumanMessage(content=prompt))
            self.messages.append(AIMessage(content=response))
            return response
        except Exception as e:
            return f"Error al resumir el artículo: {str(e)}"
    
    def format_article_response(self, articles):
        """Format the article search response with proper APA citations"""
        response = "# 📚 Resultados de la Búsqueda\n\n"
        
        # Add summary section
        response += "## 📊 Resumen de Resultados\n\n"
        response += "| Título | Año | Citaciones | Relevancia |\n"
        response += "|--------|-----|------------|------------|\n"
        for article in articles:
            citations = article.get('cited_by', 0)
            relevance = "⭐⭐⭐" if citations > 50 else "⭐⭐" if citations > 10 else "⭐"
            response += f"| [{article['title']}]({article['url']}) | {article['year']} | {citations} | {relevance} |\n"
        
        response += "\n## 📖 Artículos Encontrados\n\n"
        
        # Add articles with inline citations
        for i, article in enumerate(articles, 1):
            authors = article.get('authors', ['Sin autor'])
            year = article.get('year', 'n.d.')
            title = article.get('title', '')
            journal = article.get('journal', '')
            url = article.get('url', '')
            
            # Create citation key (first author's lastname et al., year)
            citation_key = f"({authors[0].split(',')[0]} et al., {year})"
            
            response += f"### {i}. {title}\n\n"
            response += f"> 🔍 **Fuente:** _{journal}_\n\n"
            response += f"> 📎 **[Ver artículo completo]({url})**\n\n"
            
            # Add metadata section
            response += "#### ℹ️ Información del Artículo\n\n"
            response += f"- **Autores:** {', '.join(authors)}\n"
            response += f"- **Año:** {year}\n"
            response += f"- **Citado por:** {article.get('cited_by', 'N/A')} veces\n"
            if article.get('pdf_link'):
                response += f"- **PDF:** [Descargar documento]({article['pdf_link']})\n"
            response += "\n"
            
            # Add abstract section
            response += "#### 📝 Resumen\n\n"
            response += f"{article['abstract']}\n\n"
            if article['abstract'] != article.get('abstract_es', ''):
                response += "#### 🌎 Resumen en Español\n\n"
                response += f"{article['abstract_es']}\n\n"
            
            # Add quality assessment
            response += "#### ⚖️ Evaluación de Calidad\n\n"
            quality_factors = []
            if article.get('cited_by', 0) > 50:
                quality_factors.append("✅ **Alto impacto académico** - Citado frecuentemente en la literatura")
            if article.get('source') == 'PubMed':
                quality_factors.append("✅ **Indexado en PubMed** - Revisado por pares")
            if int(article.get('year', 0)) > 2020:
                quality_factors.append("✅ **Investigación reciente** - Datos actualizados")
            if not quality_factors:
                quality_factors.append("⚠️ **Requiere evaluación adicional** - Revisar metodología")
            response += "\n".join(quality_factors) + "\n\n"
            
            response += "---\n\n"
        
        # Add References section
        response += "## 📚 Referencias\n\n"
        for article in articles:
            authors = article.get('authors', ['Sin autor'])
            year = article.get('year', 'n.d.')
            title = article.get('title', '')
            journal = article.get('journal', '')
            volume = article.get('volume', '')
            issue = article.get('issue', '')
            pages = article.get('pages', '')
            doi = article.get('doi', '')
            url = article.get('url', '')
            
            # Format authors
            if len(authors) > 1:
                authors_str = ", ".join(authors[:-1]) + ", & " + authors[-1]
            else:
                authors_str = authors[0]
            
            # Create APA reference
            reference = f"- {authors_str} ({year}). **{title}**. "
            reference += f"_{journal}_"
            if volume:
                reference += f", *{volume}*"
                if issue:
                    reference += f"({issue})"
            if pages:
                reference += f", {pages}"
            if doi:
                reference += f". [https://doi.org/{doi}](https://doi.org/{doi})"
            elif url:
                reference += f". [Ver artículo]({url})"
            
            response += f"{reference}\n\n"
        
        return response

    def format_summary_response(self, article_text, metadata=None):
        """Format the article summary with proper APA citation"""
        if metadata is None:
            metadata = {}
        
        # Create citation key
        authors = metadata.get('authors', ['Sin autor'])
        year = metadata.get('year', 'n.d.')
        citation_key = f"({authors[0].split(',')[0]} et al., {year})"
        
        response = f"# 📑 Resumen del Artículo {citation_key}\n\n"
        
        # Add metadata section
        response += "## ℹ️ Información del Artículo\n\n"
        response += f"- **Título:** {metadata.get('title', 'No disponible')}\n"
        response += f"- **Autores:** {', '.join(metadata.get('authors', ['No disponible']))}\n"
        response += f"- **Año:** {metadata.get('year', 'No disponible')}\n"
        response += f"- **Revista:** {metadata.get('journal', 'No disponible')}\n\n"
        
        # Add analysis sections
        response += "## 📊 Análisis Detallado\n\n"
        
        sections = [
            ("🎯 Objetivo del Estudio", "Describe el propósito principal y los objetivos específicos de la investigación."),
            ("🔬 Metodología", "Detalla el diseño del estudio, población, intervenciones y métodos de análisis."),
            ("📈 Resultados Principales", "Presenta los hallazgos más importantes y su significancia estadística."),
            ("💡 Conclusiones", "Resume las interpretaciones principales y las implicaciones para la práctica."),
            ("⚠️ Limitaciones", "Discute las restricciones y posibles sesgos del estudio.")
        ]
        
        for title, description in sections:
            response += f"### {title}\n\n"
            response += f"_{description}_\n\n"
        
        # Add reference
        response += "## 📚 Referencias\n\n"
        title = metadata.get('title', 'Sin título')
        journal = metadata.get('journal', '')
        volume = metadata.get('volume', '')
        issue = metadata.get('issue', '')
        pages = metadata.get('pages', '')
        doi = metadata.get('doi', '')
        url = metadata.get('url', '')
        
        # Format authors for reference
        if len(authors) > 1:
            authors_str = ", ".join(authors[:-1]) + ", & " + authors[-1]
        else:
            authors_str = authors[0]
        
        # Create APA reference
        reference = f"- {authors_str} ({year}). **{title}**. "
        reference += f"_{journal}_"
        if volume:
            reference += f", *{volume}*"
            if issue:
                reference += f"({issue})"
        if pages:
            reference += f", {pages}"
        if doi:
            reference += f". [https://doi.org/{doi}](https://doi.org/{doi})"
        elif url:
            reference += f". [Ver artículo]({url})"
        
        response += f"{reference}\n"
        
        return response

    def get_response(self, user_input):
        # Check if the input is a paper search request
        if "buscar artículos sobre" in user_input.lower():
            query = user_input.replace("buscar artículos sobre", "").strip()
            
            # Check if the user wants English results
            language = "en" if "en inglés" in user_input.lower() else "es"
            papers = self.search_papers(query, language)
            
            if isinstance(papers, str):  # Error occurred
                return papers
            
            response = self.format_article_response(papers)
            
            # Add a summary table at the top
            response += "### Resumen de Resultados\n"
            response += "| Título | Año | Citaciones | Relevancia |\n"
            response += "|--------|-----|------------|------------|\n"
            for paper in papers:
                citations = paper.get('cited_by', 0)
                relevance = "Alta" if citations > 50 else "Media" if citations > 10 else "Por evaluar"
                response += f"| [{paper['title']}]({paper['url']}) | {paper['year']} | {citations} | {relevance} |\n"
            
            response += "\n### Análisis Detallado de los Artículos\n\n"
            
            for i, paper in enumerate(papers, 1):
                response += f"#### {i}. {paper['title']}\n"
                if paper['title'] != paper['title_es']:
                    response += f"**Traducción:** {paper['title_es']}\n"
                response += f"**Autores:** {', '.join(paper['authors'])}\n"
                response += f"**Año:** {paper['year']}\n"
                response += f"**Fuente:** {paper.get('source', 'Desconocida')}\n"
                if paper.get('cited_by'):
                    response += f"**Citado por:** {paper['cited_by']} veces\n"
                response += f"**URL:** [{paper['url']}]({paper['url']})\n"
                if paper.get('pdf_link'):
                    response += f"**PDF:** [Descargar PDF]({paper['pdf_link']})\n"
                
                response += "\n**Resumen Original:**\n"
                response += f"{paper['abstract']}\n\n"
                if paper['abstract'] != paper['abstract_es']:
                    response += "**Resumen en Español:**\n"
                    response += f"{paper['abstract_es']}\n\n"
                
                # Add detailed summary
                response += "**Análisis Detallado:**\n"
                if paper.get('url'):
                    summary = self.summarize_paper(paper['abstract'], paper['url'])
                    response += f"{summary}\n\n"
                
                # Add quality assessment
                response += "**Evaluación de Calidad:**\n"
                quality_factors = []
                if paper.get('cited_by', 0) > 50:
                    quality_factors.append("✓ Alto impacto académico")
                if paper.get('source') == 'PubMed':
                    quality_factors.append("✓ Indexado en PubMed")
                if int(paper.get('year', 0)) > 2020:
                    quality_factors.append("✓ Investigación reciente")
                if not quality_factors:
                    quality_factors.append("⚠ Requiere evaluación adicional")
                response += "\n".join(quality_factors) + "\n\n"
                
                response += "---\n\n"
            
            # Add final recommendations
            response += "### Recomendaciones Finales\n"
            analysis = self.analyze_papers(papers)
            response += analysis + "\n\n"
            
            # Add references section
            response += "### Referencias\n"
            for i, paper in enumerate(papers, 1):
                response += f"{i}. {', '.join(paper['authors'])} ({paper['year']}). [{paper['title']}]({paper['url']}). {paper.get('source', 'Fuente no especificada')}.\n"
            
            self.messages.append(HumanMessage(content=user_input))
            self.messages.append(AIMessage(content=response))
            return response
        
        # Check if the input is a request for a download link
        elif "obtener enlace de descarga para" in user_input.lower():
            url = user_input.replace("obtener enlace de descarga para", "").strip()
            response = self.get_download_link(url)
            self.messages.append(HumanMessage(content=user_input))
            self.messages.append(AIMessage(content=response))
            return response
        
        # Check if the input is a request for paper summarization
        elif "resumir este artículo" in user_input.lower():
            paper_text = user_input.replace("resumir este artículo", "").strip()
            response = self.format_summary_response(paper_text)
            self.messages.append(HumanMessage(content=user_input))
            self.messages.append(AIMessage(content=response))
            return response
        
        # General conversation
        else:
            try:
                # Modify the input to force citation of sources
                enhanced_input = f"{user_input}\n\nPor favor, respalda tu respuesta con fuentes académicas relevantes y proporciona enlaces a los artículos citados."
                response = self.chain.invoke(enhanced_input)
                self.messages.append(HumanMessage(content=user_input))
                self.messages.append(AIMessage(content=response))
                return response
            except Exception as e:
                return f"Lo siento, pero encontré un error: {str(e)}" 
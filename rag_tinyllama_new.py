# import json
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from llama_cpp import Llama
# from typing import List, Dict, Tuple, Optional
# import re
# from nltk.corpus import stopwords
# from collections import Counter
# import nltk
# from nltk.corpus import words as nltk_words 
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# import random
# import os
# from flask import Flask, render_template, request, jsonify

# try:
#     nltk.download('stopwords', quiet=True)
#     nltk.download('words', quiet=True) # Ensure this is downloaded once
# except:
#     pass

# STOPWORDS = set(stopwords.words('english'))

# class TextbookRAG:
#     def __init__(
#         self,
#         index_file: str = "faiss_index.index",
#         chunks_file: str = "faiss_index_chunks_with_improved_tags.json",
#         embedding_model: str = "./my_local_model",
#         llama_model_path: str = "TinyLLaMA-1.1B-Chat.gguf"
#     ):
#         self.index_file = index_file
#         self.chunks_file = chunks_file
#         self.embedding_model_name = embedding_model
#         self.llama_model_path = llama_model_path

#         # Cache for summarized chunks
#         self.summary_cache = {}

#         self._initialize_greeting_system()
#         self._load_index()
#         self._load_embedding_model()
#         self._load_llm()
#         self._initialize_tfidf()
        
#         print("✅ Enhanced RAG system initialized successfully!")

#     def _initialize_greeting_system(self):
#         """Initialize greeting detection patterns and responses"""
#         # Common greeting patterns
#         self.greeting_patterns = [
#             r'\b(hi|hello|hey|greetings|good morning|good afternoon|hiiiiiiiiii|good evening)\b',
#             r'\b(hola|namaste|salaam|adaab)\b',
#             r'\b(what\'s up|whats up|wassup|sup)\b',
#             r'\b(how are you|how do you do)\b',
#             r'\b(nice to meet you|pleasure to meet you)\b'
#         ]
        
#         # Farewell patterns
#         self.farewell_patterns = [
#             r'\b(bye|goodbye|see you|farewell|take care|catch you later)\b',
#             r'\b(thanks|thank you|thx)\b.*\b(bye|goodbye)\b',
#             r'\b(good night|goodnight)\b'
#         ]
        
#         # Greeting responses
#         self.greeting_responses = [
#             "Hi there! 👋 I'm your Social Science Assistant Bot! Ask me anything about your social science chapters and I'll provide detailed explanations!",
            
#             "Hello! 🎓 Welcome to your personal Social Science learning companion! I can help you understand concepts from your Social Science textbook. What would you like to learn about today?",
            
#             "Hey! 📚 I'm your Social Science Bot, ready to help you explore the fascinating world of social studies!",
            
#             "Greetings! 🌟 I'm here to make your Social Science learning journey easier and more interesting! I can explain topics from your textbooks. What topic interests you?",
            
#             "Hi! 👨‍🏫 I'm your dedicated Social Science tutor bot! Feel free to ask me questions about any chapter or topic you're studying!"
#         ]
        
#         # Farewell responses
#         self.farewell_responses = [
#             "Goodbye! 👋 Keep learning and exploring the world of Social Science! Feel free to come back anytime you need help with your studies!",
            
#             "See you later! 📖 Remember, learning Social Science helps us understand our world better. Happy studying!",
            
#             "Take care! 🌟 I hope I helped you learn something new today. Keep asking questions and stay curious about the world around you!",
            
#             "Bye! 🎓 Don't forget to review what you've learned. Social Science is all about understanding society, history, and our place in the world. Good luck with your studies!",
            
#             "Farewell! 📚 Keep exploring the amazing stories of human civilization and our planet. I'll be here whenever you need help with Social Science!"
#         ]

#     def _is_greeting(self, text: str) -> bool:
#         """Check if the input is a greeting, including stretched or repeated variants"""
#         text_lower = text.lower().strip()

#         # Normalize stretched greetings
#         stretched_patterns = {
#         r'^h+i+$': 'hi',
#         r'^h+e+y+$': 'hey',
#         r'^h+e+l+o+$': 'hello',
#         r'^h+e+l+l+o+$': 'hello',
#         r'^n+a+m+a+s+t+e+$': 'namaste',
#         r'^g+o+o+d+\s*(morning|evening|afternoon)+$': 'good greeting',
#         r'^(hi)+$': 'hi',
#         r'^(hey)+$': 'hey',
#         r'^(hello)+$': 'hello',
#         r'^(namaste)+$': 'namaste'
#         }

#         for pattern in stretched_patterns:
#             if re.fullmatch(pattern, text_lower):
#                 return True

#         # Match only if the input starts with a greeting phrase
#         for pattern in self.greeting_patterns:
#             if re.match(pattern, text_lower, re.IGNORECASE):
#                 return True

#         # Exact short greeting match
#         simple_greetings = ['hi', 'hello', 'hey', 'hola', 'namaste']
#         if text_lower in simple_greetings:
#             return True

#         return False



#     def _is_farewell(self, text: str) -> bool:
#         """Check if the input is a farewell"""
#         text_lower = text.lower().strip()
        
#         for pattern in self.farewell_patterns:
#             if re.search(pattern, text_lower, re.IGNORECASE):
#                 return True
                
#         simple_farewells = ['bye', 'goodbye', 'thanks', 'thank you']
#         if text_lower in simple_farewells:
#             return True
            
#         return False

#     def _is_descriptive_query(self, question: str) -> bool:
#         """Detect if the question requires descriptive/detailed explanation"""
#         question_lower = question.lower().strip()

#         # Descriptive keywords that require detailed explanation
#         desc_keywords = [
#             'describe', 'explain', 'detail', 'elaborate', 'discuss', 'analyze', 'why', 'how',
#             'importance', 'significance', 'role', 'impact', 'causes', 'effects', 'consequences',
#             'features', 'characteristics', 'advantages', 'disadvantages', 'benefits', 'drawbacks'
#         ]

#         # Check for descriptive keywords
#         if any(keyword in question_lower for keyword in desc_keywords):
#             return True

#         # Short topic-based questions (likely need detailed explanation)
#         # e.g., "World War 2", "French Revolution", "Democracy"
#         if len(question.split()) <= 4 and not any(q in question_lower for q in ['what', 'when', 'where', 'who', 'which']):
#             return True
        
#         # Questions starting with "Tell me about..."
#         if question_lower.startswith(('tell me about', 'tell about')):
#             return True

#         return False

#     def _get_greeting_response(self) -> str:
#         """Get a random greeting response"""
#         return random.choice(self.greeting_responses)

#     def _get_farewell_response(self) -> str:
#         """Get a random farewell response"""
#         return random.choice(self.farewell_responses)

#     def _load_index(self):
#         try:
#             print("📂 Loading FAISS index and chunks...")
#             self.index = faiss.read_index(self.index_file)
#             with open(self.chunks_file, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#             self.chunks = [entry["content"] for entry in data]
#             self.metadata = data
#             self.raw_chunks = data
#             print(f"✅ Loaded {len(self.chunks)} chunks with metadata and tags")
#         except Exception as e:
#             raise Exception(f"❌ Error loading index: {e}")

#     def _load_embedding_model(self):
#         try:
#             print(f"🤖 Loading embedding model from: {self.embedding_model_name}")
            
#             # Check if it's a local path
#             if os.path.exists(self.embedding_model_name):
#                 print("📁 Loading from local directory...")
#                 self.embedding_model = SentenceTransformer(self.embedding_model_name)
#             else:
#                 print("🌐 Loading from HuggingFace (will download)...")
#                 self.embedding_model = SentenceTransformer(self.embedding_model_name)
                
#             print("✅ Embedding model loaded successfully")
#         except Exception as e:
#             print(f"❌ Error loading embedding model: {e}")
#             # Fallback to online model
#             try:
#                 print("🔄 Falling back to online model...")
#                 self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
#                 print("✅ Fallback model loaded")
#             except Exception as e2:
#                 raise Exception(f"❌ Error loading both local and online models: {e2}")


#     def _load_llm(self):
#         try:
#             print(f"🧠 Loading TinyLLaMA via llama-cpp from: {self.llama_model_path}")
#             self.llm = Llama(
#                 model_path=self.llama_model_path,
#                 n_ctx=2048,
#                 n_threads=6,
#                 n_gpu_layers=20, # Adjust based on your GPU
#                 verbose=False
#             )
#             print("✅ TinyLLaMA loaded")
#         except Exception as e:
#             print(f"❌ Failed to load TinyLLaMA: {e}")
#             self.llm = None

#     def _initialize_tfidf(self):
#         """Initialize TF-IDF vectorizer for tag similarity"""
#         try:
#             all_tags = []
#             for entry in self.raw_chunks:
#                 tags = entry.get("tags", [])
#                 if tags:
#                     all_tags.append(" ".join(tags))
#                 else:
#                     all_tags.append("")
            
#             self.tfidf_vectorizer = TfidfVectorizer(
#                 stop_words='english',
#                 ngram_range=(1, 3),
#                 max_features=1000
#             )
#             self.tag_vectors = self.tfidf_vectorizer.fit_transform(all_tags)
#             print("✅ TF-IDF vectorizer initialized for tag similarity")
#         except Exception as e:
#             print(f"⚠️ TF-IDF initialization failed: {e}")
#             self.tfidf_vectorizer = None
#             self.tag_vectors = None

#     def extract_question_keywords(self, question: str) -> List[str]:
#         """Extract meaningful keywords from question"""
#         # Remove common question words
#         question_stopwords = {'what', 'how', 'why', 'when', 'where', 'who', 'which', 
#                             'explain', 'describe', 'define', 'tell', 'give', 'examples'}
        
#         words = re.findall(r'\w+', question.lower())
#         keywords = [word for word in words 
#                    if word not in STOPWORDS 
#                    and word not in question_stopwords 
#                    and len(word) > 2]
        
#         return keywords

#     def filter_chunks_by_enhanced_tags(self, question: str, similarity_threshold: float = 0.1) -> Tuple[Optional[faiss.IndexFlatL2], List[str], List[Dict]]:
#         """
#         Enhanced filtering using multiple strategies:
#         1. Exact keyword matching
#         2. Partial keyword matching 
#         3. TF-IDF similarity
#         4. Semantic similarity (though less direct here, more in main retrieval)
#         """
#         question_keywords = self.extract_question_keywords(question)
#         if not question_keywords:
#             return None, [], []
        
#         print(f"🔍 Extracted keywords: {question_keywords}")
        
#         scored_entries = []
        
#         for entry in self.raw_chunks:
#             tags = entry.get("tags", [])
#             if not tags:
#                 continue
                
#             score = 0
            
#             # Strategy 1: Exact keyword matching in tags
#             tags_lower = [tag.lower() for tag in tags]
#             tags_text = " ".join(tags_lower)
            
#             exact_matches = sum(1 for keyword in question_keywords if keyword in tags_text)
#             score += exact_matches * 3  # High weight for exact matches
            
#             # Strategy 2: Partial matching (keywords as substrings)
#             partial_matches = sum(1 for keyword in question_keywords 
#                                 for tag in tags_lower if keyword in tag)
#             score += partial_matches * 2  # Medium weight for partial matches
            
#             # Strategy 3: TF-IDF similarity
#             if self.tfidf_vectorizer and self.tag_vectors is not None:
#                 try:
#                     question_vector = self.tfidf_vectorizer.transform([question])
#                     tag_vector_idx = self.raw_chunks.index(entry) # Get index of current entry in raw_chunks
#                     tfidf_sim = cosine_similarity(question_vector, self.tag_vectors[tag_vector_idx])[0][0]
#                     score += tfidf_sim * 5  # Weight TF-IDF similarity
#                 except Exception as e:
#                     print(f"TF-IDF calculation error for entry: {e}")
#                     pass # Continue even if TF-IDF fails for one entry
            
#             # Strategy 4: Check content for keywords as backup
#             content_lower = entry.get("content", "").lower()
#             content_matches = sum(1 for keyword in question_keywords if keyword in content_lower)
#             score += content_matches * 0.5  # Low weight for content matches
            
#             if score > 0:
#                 scored_entries.append((score, entry))
        
#         # Sort by score and take top entries
#         scored_entries.sort(key=lambda x: x[0], reverse=True)
        
#         # Dynamic threshold: take at least top 20% or minimum 3 entries
#         min_entries = min(3, len(scored_entries))
#         top_20_percent = max(min_entries, len(scored_entries) // 5)
        
#         filtered_entries = [entry for score, entry in scored_entries[:top_20_percent]]
        
#         print(f"📊 Tag filtering: {len(filtered_entries)} chunks selected from {len(self.raw_chunks)}")
#         if filtered_entries:
#             print(f"   Top scores: {[round(score, 2) for score, _ in scored_entries[:min(5, len(scored_entries))]]}")
        
#         if not filtered_entries:
#             print("⚠️ No chunks matched via enhanced tag filtering")
#             return None, [], []

#         filtered_chunks = [entry["content"] for entry in filtered_entries]
#         filtered_metadata = filtered_entries

#         # Create temporary FAISS index
#         embeddings = self.embedding_model.encode(filtered_chunks, convert_to_numpy=True).astype('float32')
#         index = faiss.IndexFlatL2(embeddings.shape[1])
#         index.add(embeddings)

#         return index, filtered_chunks, filtered_metadata

#     def retrieve_chunks(self, query: str, k: int = 5, index_override=None, chunks_override=None, metadata_override=None) -> List[Dict]:
#         """Enhanced retrieval with fallback mechanism"""
#         try:
#             query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
#             index = index_override if index_override is not None else self.index    
#             chunks = chunks_override if chunks_override is not None else self.chunks
#             metadata = metadata_override if metadata_override is not None else self.metadata

#             # Ensure k doesn't exceed available chunks
#             k = min(k, len(chunks))
            
#             distances, indices = index.search(query_embedding.astype('float32'), k)
#             results = []
            
#             for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
#                 if idx < len(chunks): # Ensure index is within bounds of current chunks list
#                     results.append({
#                         "rank": i + 1,
#                         "chunk": chunks[idx],
#                         "metadata": metadata[idx],
#                         "distance": float(distance),
#                         "similarity": 1 / (1 + distance) # Inverse relationship: lower distance means higher similarity
#                     })
#             return results
#         except Exception as e:
#             print(f"❌ Error retrieving chunks: {e}")
#             return []

#     def build_context_from_chunks(self, query: str, context_chunks: List[str], max_context_chars: int = 2500) -> str:
#         """Smartly build context with improved ranking"""
#         if not context_chunks:
#             return ""
            
#         query_keywords = self.extract_question_keywords(query)
#         chunk_scores = []

#         for chunk in context_chunks:
#             score = 0
#             chunk_lower = chunk.lower()
            
#             # Score by keyword presence
#             for keyword in query_keywords:
#                 if keyword in chunk_lower:
#                     score += chunk_lower.count(keyword)
            
#             # Boost score for longer, more detailed chunks (normalized)
#             score += len(chunk) / 1000  
            
#             chunk_scores.append((score, chunk))

#         # Sort by relevance
#         chunk_scores.sort(key=lambda x: x[0], reverse=True)

#         # Build context sentence by sentence from top-scoring chunks
#         final_context = ""
#         total_chars = 0
        
#         for score, chunk in chunk_scores:
#             sentences = re.split(r'(?<=[.?!])\s+', chunk.strip())
#             for sentence in sentences:
#                 sentence = sentence.strip()
#                 if not sentence:
#                     continue
                    
#                 sentence_len = len(sentence)
#                 if total_chars + sentence_len + 1 <= max_context_chars:
#                     final_context += sentence + " "
#                     total_chars += sentence_len + 1
#                 else:
#                     break # Current sentence would exceed max_context_chars, stop adding
                    
#             if total_chars >= max_context_chars:
#                 break # Max context reached, stop processing further chunks

#         return final_context.strip()

#     def generate_answer(self, query: str, context_chunks: List[str], max_length: int = 300) -> str:
#         """Enhanced answer generation with better prompting"""
#         if not self.llm:
#             return self._generate_simple_answer(query, context_chunks)

#         try:
#             context = self.build_context_from_chunks(query, context_chunks)
            
#             if not context.strip():
#                 return "I couldn't find relevant information in the textbook."

#             # Improved prompt
#             prompt = f"""You are a knowledgeable teacher helping a student. Answer the question using ONLY the information from the textbook provided below.

# Be specific and detailed in your explanation. Include examples when they are mentioned in the text.

# Answer the question using ONLY the information from the textbook content provided below
#  If the textbook content does not contain relevant information to answer the question, explicitly state: "This information is not available in the provided textbook content." Do NOT generate or infer answers beyond the provided context.

# Textbook Content:
# {context}

# Student Question: {query}

# Teacher's Answer:"""
#             tokens = self.llm.tokenize(prompt.encode("utf-8"))
#             print(f"🧮 Prompt Token Count: {len(tokens)} | Max Output Tokens: {max_length}")
#             result = self.llm(
#                 prompt,
#                 max_tokens=max_length,
#                 temperature=0.1,
#                 top_p=0.9,
#                 repeat_penalty=1.1,
#                 stop=["Student Question:", "Textbook Content:", "Teacher's Answer:"],
#                 echo=False
#             )

#             answer = result["choices"][0]["text"].strip()
                        
#             if answer:
#                 # Clean up the answer (remove duplicates, short sentences, etc.)
#                 sentences = [s.strip() for s in answer.split('.') if s.strip()]
#                 unique_sentences = []
#                 seen = set()
        
#                 for sentence in sentences[:8]: # Limit to a reasonable number of sentences
#                     sentence_lower = sentence.lower()
#                     if sentence_lower not in seen and len(sentence) > 10: # Avoid very short sentences
#                         unique_sentences.append(sentence)
#                         seen.add(sentence_lower)
        
#                 final_answer = '. '.join(unique_sentences)
#                 if final_answer and not final_answer.endswith('.'):
#                     final_answer += '.'
            
#                 # Final check for relevance (optional, but good for robustness)
#                 if "not available in the provided textbook content" in final_answer.lower() or "not found" in final_answer.lower():
#                     return "This information is not available in the provided textbook content."
                
#                 return final_answer if final_answer else "Could not generate a clear answer."
    
#             return self._generate_simple_answer(query, context_chunks)

#         except Exception as e:
#             print(f"⚠️ Error generating with TinyLLaMA: {e}")
#             return self._generate_simple_answer(query, context_chunks)

#     def _generate_simple_answer(self, query: str, context_chunks: List[str]) -> str:
#         """Enhanced fallback answer generation (extracts from chunks)"""
#         if not context_chunks:
#             return "I couldn't find relevant information in the textbook."
        
#         # Combine top few chunks for fallback
#         combined_text = " ".join(context_chunks[:3]) 
#         sentences = re.split(r'(?<=[.?!])\s+', combined_text.strip())
        
#         query_keywords = self.extract_question_keywords(query)
        
#         # Score sentences by relevance
#         sentence_scores = []
#         for sentence in sentences:
#             sentence = sentence.strip()
#             if len(sentence) < 10: # Ignore very short sentences
#                 continue
                
#             score = 0
#             sentence_lower = sentence.lower()
            
#             # Score by keyword presence
#             for keyword in query_keywords:
#                 if keyword in sentence_lower:
#                     score += 1
            
#             # Boost informative sentences
#             if any(word in sentence_lower for word in ['example', 'such as', 'including', 'like']):
#                 score += 0.5
                
#             sentence_scores.append((score, sentence))
        
#         if sentence_scores:
#             sentence_scores.sort(key=lambda x: x[0], reverse=True) # Sort by score
#             top_sentences = [sent[1] for sent in sentence_scores[:6]] # Take top 6 sentences
#             result = '. '.join(top_sentences).strip()
#             if result and not result.endswith('.'):
#                 result += '.'
#             return result
        
#         # Ultimate fallback if no relevant sentences found
#         fallback = '. '.join(sentences[:4]).strip()
#         if fallback and not fallback.endswith('.'):
#             fallback += '.'
#         return fallback or "I couldn't find relevant information in the textbook."


#     def query(self, question: str, k: int = 5, verbose: bool = False) -> Dict:
#         """Enhanced query with better filtering and fallback"""
#         if verbose:
#             print(f"\n🔍 Query: {question}")
#             print("-" * 50)

#         # Check for greetings
#         if self._is_greeting(question):
#             greeting_response = self._get_greeting_response()
#             if verbose:
#                 print(f"👋 Greeting detected!")
#                 print(f"🤖 Response: {greeting_response}")
#             return {
#                 "question": question,
#                 "answer": greeting_response,
#                 "sources": [],
#                 "retrieved_chunks": [],
#                 "type": "greeting"
#             }
        
#         # Check for farewells
#         if self._is_farewell(question):
#             farewell_response = self._get_farewell_response()
#             if verbose:
#                 print(f"👋 Farewell detected!")
#                 print(f"🤖 Response: {farewell_response}")
#             return {
#                 "question": question,
#                 "answer": farewell_response,
#                 "sources": [],
#                 "retrieved_chunks": [],
#                 "type": "farewell"
#             }

#         # Regular query processing
#         if verbose:
#             print(f"📚 Processing Social Science query...")

#         # Try enhanced tag filtering first
#         faiss_index, filtered_chunks, filtered_metadata = self.filter_chunks_by_enhanced_tags(question)
        
#         if not filtered_chunks:
#             if verbose:
#                 print("⚠️ Tag filtering failed, using full index as fallback")
#             # Fallback to full index
#             retrieved_chunks = self.retrieve_chunks(question, k=k)
#         else:
#             retrieved_chunks = self.retrieve_chunks(
#                 question, k=k, 
#                 index_override=faiss_index, 
#                 chunks_override=filtered_chunks, 
#                 metadata_override=filtered_metadata
#             )

#         if not retrieved_chunks:
#             polite_responses = [
#                 "Hmm... I couldn’t find this in the textbook, but it sounds important!",
#                 "Sorry, I don’t have this information in the provided materials.",
#                 "This topic doesn't appear in the textbook content I'm trained on. Maybe try rephrasing or asking something else?",
#                 "I don’t have this covered, but I’d love to help with anything from your Social Science chapters!"
#             ]
#             fallback_response = random.choice(polite_responses)
#             return {
#                 "question": question,
#                 "answer": fallback_response,
#                 "sources": [],
#                 "retrieved_chunks": []
#             }

#         if verbose:
#             print(f"📚 Retrieved {len(retrieved_chunks)} relevant chunks")
#             for i, chunk_info in enumerate(retrieved_chunks[:3]):  # Show top 3
#                 meta = chunk_info["metadata"]
#                 similarity = chunk_info["similarity"]
#                 source = meta.get("source", "Unknown")
#                 tags = meta.get("tags", [])[:5]  # Show first 5 tags
                
#                 print(f"\n🔖 CHUNK #{i+1} (Similarity: {similarity:.4f})")
#                 print(f"   📂 Source: {source}")
#                 print(f"   🏷️ Tags: {', '.join(tags)}")
#                 print(f"   📄 Content: {chunk_info['chunk'][:200]}...")

#         # Only pass the top chunk for context to TinyLlama as it was designed for that based on previous convo
#         # Also, the build_context_from_chunks will handle selecting relevant sentences from the top K chunks retrieved
#         # before passing to LLM within generate_answer function.
#         # So passing only the top chunk to generate_answer if it's not a descriptive query based on earlier conversation.
#         # If it is a descriptive query, pass all retrieved chunks.
#         if self._is_descriptive_query(question):
#              print(f"📝 Detected a descriptive query. Sending all {len(retrieved_chunks)} retrieved chunks to LLM for context building.")
#              context_chunks_for_llm = [chunk_info["chunk"] for chunk_info in retrieved_chunks]
#         else:
#              print(f"📝 Detected a concise query. Sending top 1 chunk to LLM.")
#              context_chunks_for_llm = [retrieved_chunks[0]["chunk"]]


#         answer = self.generate_answer(question, context_chunks_for_llm)

#         if verbose:
#             print(f"\n💡 Answer: {answer}")

#         return {
#             "question": question,
#             "answer": answer,
#             "sources": [chunk_info["metadata"] for chunk_info in retrieved_chunks[:3]], # Still show top 3 sources
#             "retrieved_chunks": retrieved_chunks
#         }

#     def search_for_content(self, search_term: str, max_results: int = 5):
#         """Enhanced content search"""
#         print(f"\n🔍 SEARCHING FOR: '{search_term}'")
#         print("=" * 60)
        
#         found_chunks = []
#         search_lower = search_term.lower()
        
#         for i, entry in enumerate(self.raw_chunks):
#             chunk = entry["content"]
#             tags = entry.get("tags", [])
            
#             # Search in content
#             if search_lower in chunk.lower():
#                 found_chunks.append({
#                     "index": i,
#                     "chunk": chunk,
#                     "metadata": entry,
#                     "match_type": "content",
#                     "relevance": chunk.lower().count(search_lower)
#                 })
            
#             # Search in tags
#             elif any(search_lower in tag.lower() for tag in tags):
#                 found_chunks.append({
#                     "index": i,
#                     "chunk": chunk,
#                     "metadata": entry,
#                     "match_type": "tags",
#                     "relevance": sum(1 for tag in tags if search_lower in tag.lower())
#                 })
        
#         # Sort by relevance
#         found_chunks.sort(key=lambda x: x["relevance"], reverse=True)
#         found_chunks = found_chunks[:max_results]
        
#         if found_chunks:
#             print(f"✅ Found '{search_term}' in {len(found_chunks)} chunks:")
#             for i, item in enumerate(found_chunks):
#                 meta = item["metadata"]
#                 source = meta.get("source", "Unknown")
#                 tags = meta.get("tags", [])[:3]
                
#                 print(f"\n📄 MATCH #{i+1} (Type: {item['match_type']}, Relevance: {item['relevance']})")
#                 print(f"   📂 Source: {source}")
#                 print(f"   🏷️ Tags: {', '.join(tags)}")
#                 print(f"   📝 Content: {item['chunk'][:300]}...")
#                 print("   " + "-" * 50)
#         else:
#             print(f"❌ '{search_term}' not found in any chunks")
        
#         return found_chunks

#     def interactive_mode(self):
#         """Enhanced interactive mode"""
#         print("\n🎓 Welcome to the Enhanced Textbook RAG System!")
#         print("Commands:")
#         print("  - Ask any question directly")
#         print("  - 'search <term>' - Search for specific content")
#         print("  - 'debug <question>' - Debug mode with detailed analysis")
#         print("  - 'quit' - Exit")
#         print("-" * 60)
#         print(f"\n🤖 {self._get_greeting_response()}")
#         while True:
#             try:
#                 user_input = input("\n❓ Your input: ").strip()
#                 if user_input.lower() in ['quit', 'exit', 'q']:
#                     print("👋 Goodbye!")
#                     break
                    
#                 if not user_input:
#                     print("🤖 Please enter a question or command.")
#                     continue

#                 if user_input.lower().startswith('search '):
#                     search_term = user_input[7:].strip()
#                     self.search_for_content(search_term)
#                     continue
                
#                 if user_input.lower().startswith('debug '):
#                     question = user_input[6:].strip()
#                     # Add debug functionality here
#                     result = self.query(question, verbose=True, k=8)
#                     print(f"\n🤖 Bot: {result['answer']}")
#                 else:
#                     result = self.query(user_input, verbose=True)
#                     print(f"\n🤖 Bot: {result['answer']}")
#                 print("\n" + "=" * 60)
#             except KeyboardInterrupt:
#                 print(f"\n\n🤖 {self._get_farewell_response()}")
#                 break
#             except Exception as e:
#                 print(f"❌ Error: {e}")

# # --- Flask Integration ---
# app = Flask(__name__)
# rag_system = None # Initialize globally

# @app.before_request
# def initialize_rag_system():
#     global rag_system
#     if rag_system is None:
#         try:
#             print("🚀 Initializing Enhanced RAG system for Flask app...")
#             # Adjust these paths as necessary for your environment
#             rag_system = TextbookRAG(
#                 index_file="faiss_index.index",
#                 chunks_file="faiss_index_chunks_with_improved_tags.json",
#                 embedding_model="./my_local_model",
#                 llama_model_path=r"C:/Users/Siansha Bhushan/Desktop/class8_2/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
#             )
#             print("✅ RAG system ready for Flask requests!")
#         except Exception as e:
#             print(f"❌ FATAL ERROR: Could not initialize RAG system: {e}")
#             rag_system = None # Ensure it remains None if initialization fails

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/ask', methods=['POST'])
# def ask():
#     if rag_system is None:
#         return jsonify({"answer": "Error: RAG system not initialized. Please check server logs.", "sources": []}), 500
    
#     user_question = request.json.get('question')
#     if not user_question:
#         return jsonify({"answer": "Please provide a question.", "sources": []}), 400

#     print(f"\n--- Web Query Received: {user_question} ---")
#     response = rag_system.query(user_question, verbose=True) # Set verbose to True for console output during web queries

#     # Extract relevant info for JSON response
#     answer = response.get("answer", "I could not find an answer.")
#     sources_raw = response.get("sources", [])
    
#     # Format sources for display
#     formatted_sources = []
#     if sources_raw:
#         # Use a set to keep track of unique source names/files to avoid duplicates
#         seen_sources = set()
#         for source_meta in sources_raw:
#             source_name = source_meta.get("source", "Unknown Source")
#             if source_name not in seen_sources:
#                 formatted_sources.append({"name": source_name, "tags": source_meta.get("tags", [])})
#                 seen_sources.add(source_name)

#     return jsonify({"answer": answer, "sources": formatted_sources})

# if __name__ == '__main__':
#     # Flask app will handle initialization via @app.before_request
#     print("🚀 Starting Flask application...")
#     app.run(debug=True, host='0.0.0.0', port=5000)

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
from typing import List, Dict, Tuple, Optional
import re
from nltk.corpus import stopwords
from collections import Counter
import nltk
from nltk.corpus import words as nltk_words

# Ensure this is downloaded once
nltk.download('words')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
try:
    nltk.download('stopwords', quiet=True)
except:
    pass

STOPWORDS = set(stopwords.words('english'))

class TextbookRAG:
    def __init__(
        self,
        index_file: str = "faiss_index.index",
        chunks_file: str = "faiss_index_chunks_with_improved_tags.json",
        embedding_model: str = "./my_local_model",
        llama_model_path: str = "TinyLLaMA-1.1B-Chat.gguf"
    ):
        self.index_file = index_file
        self.chunks_file = chunks_file
        self.embedding_model_name = embedding_model
        self.llama_model_path = llama_model_path

        # Cache for summarized chunks
        self.summary_cache = {}

        self._initialize_greeting_system()
        self._load_index()
        self._load_embedding_model()
        self._load_llm()
        self._initialize_tfidf()
        

        print("✅ Enhanced RAG system initialized successfully!")

    def _initialize_greeting_system(self):
        """Initialize greeting detection patterns and responses"""
        # Common greeting patterns
        self.greeting_patterns = [
            r'\b(hi|hello|hey|greetings|good morning|good afternoon|hiiiiiiiiii|good evening)\b',
            r'\b(hola|namaste|salaam|adaab)\b',
            r'\b(what\'s up|whats up|wassup|sup)\b',
            r'\b(how are you|how do you do)\b',
            r'\b(nice to meet you|pleasure to meet you)\b'
        ]
        
        # Farewell patterns
        self.farewell_patterns = [
            r'\b(bye|goodbye|see you|farewell|take care|catch you later)\b',
            r'\b(thanks|thank you|thx)\b.*\b(bye|goodbye)\b',
            r'\b(good night|goodnight)\b'
        ]
        
        # Greeting responses
        self.greeting_responses = [
            "Hi there! 👋 I'm your Social Science Assistant Bot! Ask me anything about your social science chapters and I'll provide detailed explanations!",
            
            "Hello! 🎓 Welcome to your personal Social Science learning companion! I can help you understand concepts from your Social Science textbook. What would you like to learn about today?",
            
            "Hey! 📚 I'm your Social Science Bot, ready to help you explore the fascinating world of social studies!",
            
            "Greetings! 🌟 I'm here to make your Social Science learning journey easier and more interesting! I can explain topics from your textbooks. What topic interests you?",
            
            "Hi! 👨‍🏫 I'm your dedicated Social Science tutor bot! Feel free to ask me questions about any chapter or topic you're studying!"
        ]
        
        # Farewell responses
        self.farewell_responses = [
            "Goodbye! 👋 Keep learning and exploring the world of Social Science! Feel free to come back anytime you need help with your studies!",
            
            "See you later! 📖 Remember, learning Social Science helps us understand our world better. Happy studying!",
            
            "Take care! 🌟 I hope I helped you learn something new today. Keep asking questions and stay curious about the world around you!",
            
            "Bye! 🎓 Don't forget to review what you've learned. Social Science is all about understanding society, history, and our place in the world. Good luck with your studies!",
            
            "Farewell! 📚 Keep exploring the amazing stories of human civilization and our planet. I'll be here whenever you need help with Social Science!"
        ]

    def _is_greeting(self, text: str) -> bool:
        """Check if the input is a greeting, including stretched or repeated variants"""
        text_lower = text.lower().strip()

        # Normalize stretched greetings
        stretched_patterns = {
        r'^h+i+$': 'hi',
        r'^h+e+y+$': 'hey',
        r'^h+e+l+o+$': 'hello',
        r'^h+e+l+l+o+$': 'hello',
        r'^n+a+m+a+s+t+e+$': 'namaste',
        r'^g+o+o+d+\s*(morning|evening|afternoon)+$': 'good greeting',
        r'^(hi)+$': 'hi',
        r'^(hey)+$': 'hey',
        r'^(hello)+$': 'hello',
        r'^(namaste)+$': 'namaste'
        }

        for pattern in stretched_patterns:
            if re.fullmatch(pattern, text_lower):
                return True

        # Match only if the input starts with a greeting phrase
        for pattern in self.greeting_patterns:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return True

        # Exact short greeting match
        simple_greetings = ['hi', 'hello', 'hey', 'hola', 'namaste']
        if text_lower in simple_greetings:
            return True

        return False

    def _is_farewell(self, text: str) -> bool:
        """Check if the input is a farewell"""
        text_lower = text.lower().strip()
        
        for pattern in self.farewell_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
                
        simple_farewells = ['bye', 'goodbye', 'thanks', 'thank you']
        if text_lower in simple_farewells:
            return True
            
        return False

    def _is_descriptive_query(self, question: str) -> bool:
        """Detect if the question requires descriptive/detailed explanation"""
        question_lower = question.lower().strip()
        
        # Descriptive keywords that require detailed explanation
        desc_keywords = [
            'describe', 'explain', 'detail', 'elaborate', 'discuss', 'analyze',
            'why', 'how', 'importance', 'significance', 'role', 'impact',
            'causes', 'effects', 'consequences', 'features', 'characteristics',
            'advantages', 'disadvantages', 'benefits', 'drawbacks'
        ]
        
        # Check for descriptive keywords
        if any(keyword in question_lower for keyword in desc_keywords):
            return True
        
        # Short topic-based questions (likely need detailed explanation)
        # e.g., "World War 2", "French Revolution", "Democracy"
        if len(question.split()) <= 4 and not any(q in question_lower for q in ['what', 'when', 'where', 'who', 'which']):
            return True
        
        # Questions starting with "Tell me about..."
        if question_lower.startswith(('tell me about', 'tell about')):
            return True
            
        return False

    def _get_greeting_response(self) -> str:
        """Get a random greeting response"""
        return random.choice(self.greeting_responses)

    def _get_farewell_response(self) -> str:
        """Get a random farewell response"""
        return random.choice(self.farewell_responses)

    def _load_index(self):
        try:
            print("📂 Loading FAISS index and chunks...")
            self.index = faiss.read_index(self.index_file)
            with open(self.chunks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = [entry["content"] for entry in data]
            self.metadata = data
            self.raw_chunks = data
            print(f"✅ Loaded {len(self.chunks)} chunks with metadata and tags")
        except Exception as e:
            raise Exception(f"❌ Error loading index: {e}")

    def _load_embedding_model(self):
        try:
            print(f"🤖 Loading embedding model from: {self.embedding_model_name}")
            
            # Check if it's a local path
            if os.path.exists(self.embedding_model_name):
                print("📁 Loading from local directory...")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
            else:
                print("🌐 Loading from HuggingFace (will download)...")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                
            print("✅ Embedding model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            # Fallback to online model
            try:
                print("🔄 Falling back to online model...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Fallback model loaded")
            except Exception as e2:
                raise Exception(f"❌ Error loading both local and online models: {e2}")

    def _load_llm(self):
        try:
            print(f"🧠 Loading TinyLLaMA via llama-cpp from: {self.llama_model_path}")
            self.llm = Llama(
                model_path=self.llama_model_path,
                n_ctx=2048,
                n_threads=6,
                n_gpu_layers=20,
                verbose=False
            )
            print("✅ TinyLLaMA loaded")
        except Exception as e:
            print(f"❌ Failed to load TinyLLaMA: {e}")
            self.llm = None

    def _initialize_tfidf(self):
        """Initialize TF-IDF vectorizer for tag similarity"""
        try:
            all_tags = []
            for entry in self.raw_chunks:
                tags = entry.get("tags", [])
                if tags:
                    all_tags.append(" ".join(tags))
                else:
                    all_tags.append("")
            
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 3),
                max_features=1000
            )
            self.tag_vectors = self.tfidf_vectorizer.fit_transform(all_tags)
            print("✅ TF-IDF vectorizer initialized for tag similarity")
        except Exception as e:
            print(f"⚠️ TF-IDF initialization failed: {e}")
            self.tfidf_vectorizer = None
            self.tag_vectors = None

    def extract_question_keywords(self, question: str) -> List[str]:
        """Extract meaningful keywords from question"""
        # Remove common question words
        question_stopwords = {'what', 'how', 'why', 'when', 'where', 'who', 'which', 
                            'explain', 'describe', 'define', 'tell', 'give', 'examples'}
        
        words = re.findall(r'\w+', question.lower())
        keywords = [word for word in words 
                   if word not in STOPWORDS 
                   and word not in question_stopwords 
                   and len(word) > 2]
        
        return keywords

    def filter_chunks_by_enhanced_tags(self, question: str, similarity_threshold: float = 0.1) -> Tuple[Optional[faiss.IndexFlatL2], List[str], List[Dict]]:
        """
        Enhanced filtering using multiple strategies:
        1. Exact keyword matching
        2. Partial keyword matching 
        3. TF-IDF similarity
        4. Semantic similarity
        """
        question_keywords = self.extract_question_keywords(question)
        if not question_keywords:
            return None, [], []
        
        print(f"🔍 Extracted keywords: {question_keywords}")
        
        scored_entries = []
        
        for entry in self.raw_chunks:
            tags = entry.get("tags", [])
            if not tags:
                continue
                
            score = 0
            
            # Strategy 1: Exact keyword matching in tags
            tags_lower = [tag.lower() for tag in tags]
            tags_text = " ".join(tags_lower)
            
            exact_matches = sum(1 for keyword in question_keywords if keyword in tags_text)
            score += exact_matches * 3  # High weight for exact matches
            
            # Strategy 2: Partial matching (keywords as substrings)
            partial_matches = sum(1 for keyword in question_keywords 
                                for tag in tags_lower if keyword in tag)
            score += partial_matches * 2  # Medium weight for partial matches
            
            # Strategy 3: TF-IDF similarity
            if self.tfidf_vectorizer and self.tag_vectors is not None:
                try:
                    question_vector = self.tfidf_vectorizer.transform([question])
                    tag_vector = self.tag_vectors[self.raw_chunks.index(entry)]
                    tfidf_sim = cosine_similarity(question_vector, tag_vector)[0][0]
                    score += tfidf_sim * 5  # Weight TF-IDF similarity
                except:
                    pass
            
            # Strategy 4: Check content for keywords as backup
            content_lower = entry.get("content", "").lower()
            content_matches = sum(1 for keyword in question_keywords if keyword in content_lower)
            score += content_matches * 0.5  # Low weight for content matches
            
            if score > 0:
                scored_entries.append((score, entry))
        
        # Sort by score and take top entries
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        
        # Dynamic threshold: take at least top 20% or minimum 3 entries
        min_entries = min(3, len(scored_entries))
        top_20_percent = max(min_entries, len(scored_entries) // 5)
        
        filtered_entries = [entry for score, entry in scored_entries[:top_20_percent]]
        
        print(f"📊 Tag filtering: {len(filtered_entries)} chunks selected from {len(self.raw_chunks)}")
        if filtered_entries:
            print(f"   Top scores: {[round(score, 2) for score, _ in scored_entries[:5]]}")
        
        if not filtered_entries:
            print("⚠️ No chunks matched via enhanced tag filtering")
            return None, [], []

        filtered_chunks = [entry["content"] for entry in filtered_entries]
        filtered_metadata = filtered_entries

        # Create temporary FAISS index
        embeddings = self.embedding_model.encode(filtered_chunks, convert_to_numpy=True).astype('float32')
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)

        return index, filtered_chunks, filtered_metadata

    def retrieve_chunks(self, query: str, k: int = 5, index_override=None, chunks_override=None, metadata_override=None) -> List[Dict]:
        """Enhanced retrieval with fallback mechanism"""
        try:
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            index = index_override if index_override is not None else self.index    
            chunks = chunks_override if chunks_override is not None else self.chunks
            metadata = metadata_override if metadata_override is not None else self.metadata

            # Ensure k doesn't exceed available chunks
            k = min(k, len(chunks))
            
            distances, indices = index.search(query_embedding.astype('float32'), k)
            results = []
            
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx < len(chunks):
                    results.append({
                        "rank": i + 1,
                        "chunk": chunks[idx],
                        "metadata": metadata[idx],
                        "distance": float(distance),
                        "similarity": 1 / (1 + distance)
                    })
            return results
        except Exception as e:
            print(f"❌ Error retrieving chunks: {e}")
            return []
        

    def _is_nonsense(self, question: str) -> bool:
        """Detect gibberish input based on absence of known English words"""
        words = re.findall(r'\w+', question.lower())
        valid_words = [word for word in words if word not in STOPWORDS and len(word) > 2]

        known_words = set(nltk_words.words())
        known_word_count = sum(1 for word in valid_words if word in known_words)

        return known_word_count == 0


    def summarize_chunk(self, chunk: str) -> str:
        """Summarize a single chunk for descriptive queries"""
        if not self.llm:
            # Fallback: return first few sentences
            sentences = re.split(r'(?<=[.?!])\s+', chunk.strip())
            return '. '.join(sentences[:3]).strip()
        
        # Use cache to avoid re-summarizing same chunk
        chunk_hash = hash(chunk)
        if chunk_hash in self.summary_cache:
            return self.summary_cache[chunk_hash]
        
        try:
            prompt = f"""Summarize the following textbook passage in 2-3 sentences, preserving all key facts, dates, names, and important details.

Text:
{chunk}

Summary:"""

            result = self.llm(
                prompt,
                max_tokens=120,
                temperature=0.2,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["Summary:", "Text:"],
                echo=False
            )

            summary = result["choices"][0]["text"].strip()
            
            # Clean up the summary
            if summary:
                # Remove any trailing incomplete sentences
                sentences = [s.strip() for s in summary.split('.') if s.strip()]
                if sentences:
                    summary = '. '.join(sentences)
                    if not summary.endswith('.'):
                        summary += '.'
            else:
                # Fallback if summary is empty
                sentences = re.split(r'(?<=[.?!])\s+', chunk.strip())
                summary = '. '.join(sentences[:2]).strip()
            
            # Cache the summary
            self.summary_cache[chunk_hash] = summary
            return summary
            
        except Exception as e:
            print(f"⚠️ Error summarizing chunk: {e}")
            # Fallback to simple truncation
            sentences = re.split(r'(?<=[.?!])\s+', chunk.strip())
            summary = '. '.join(sentences[:2]).strip()
            self.summary_cache[chunk_hash] = summary
            return summary

    def build_descriptive_context(self, chunks: List[str], max_summary_chars: int = 4000) -> str:
        """Build comprehensive context for descriptive queries by summarizing chunks"""
        print(f"📝 Building descriptive context from {len(chunks)} chunks...")
        
        summaries = []
        total_chars = 0

        for i, chunk in enumerate(chunks):
            print(f"   Summarizing chunk {i+1}/{len(chunks)}...")
            summary = self.summarize_chunk(chunk)
            
            if summary and len(summary) > 10:  # Only add meaningful summaries
                if total_chars + len(summary) + 2 < max_summary_chars:  # +2 for newlines
                    summaries.append(summary)
                    total_chars += len(summary) + 2
                else:
                    break

        final_context = "\n\n".join(summaries)
        print(f"✅ Built descriptive context: {len(final_context)} characters from {len(summaries)} summaries")
        
        return final_context

    def build_context_from_chunks(self, query: str, context_chunks: List[str], max_context_chars: int = 2500) -> str:
        """Smartly build context with improved ranking for factual queries"""
        if not context_chunks:
            return ""
            
        query_keywords = self.extract_question_keywords(query)
        chunk_scores = []

        for chunk in context_chunks:
            score = 0
            chunk_lower = chunk.lower()
            
            # Score by keyword presence
            for keyword in query_keywords:
                if keyword in chunk_lower:
                    score += chunk_lower.count(keyword)
            
            # Boost score for longer, more detailed chunks
            score += len(chunk) / 1000  # Normalize by length
            
            chunk_scores.append((score, chunk))

        # Sort by relevance
        chunk_scores.sort(key=lambda x: x[0], reverse=True)

        # Build context sentence by sentence
        final_context = ""
        total_chars = 0
        
        for score, chunk in chunk_scores:
            sentences = re.split(r'(?<=[.?!])\s+', chunk.strip())
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                sentence_len = len(sentence)
                if total_chars + sentence_len + 1 <= max_context_chars:
                    final_context += sentence + " "
                    total_chars += sentence_len + 1
                else:
                    break
                    
            if total_chars >= max_context_chars:
                break

        return final_context.strip()

    def generate_answer(self, query: str, context_chunks: List[str], max_length: int = 300) -> str:
        """Enhanced answer generation with dynamic strategy switching"""
        if not self.llm:
            return self._generate_simple_answer(query, context_chunks)

        try:
            # 🎯 DYNAMIC STRATEGY SWITCHING
            is_descriptive = self._is_descriptive_query(query)
            
            if is_descriptive:
                print("📊 Using DESCRIPTIVE strategy (summarize + merge)")
                context = self.build_descriptive_context(context_chunks, max_summary_chars=4000)
                max_length = 400  # Allow longer answers for descriptive queries
            else:
                print("📋 Using FACTUAL strategy (top-k + 2500 char limit)")
                context = self.build_context_from_chunks(query, context_chunks, max_context_chars=2500)
                max_length = 300  # Shorter answers for factual queries
            
            if not context.strip():
                return "I couldn't find relevant information in the textbook."

            # Enhanced prompt based on query type
            if is_descriptive:
                prompt = f"""You are a knowledgeable teacher providing detailed explanations. Use the comprehensive information below to give a thorough, well-structured answer.

Include specific examples, facts, and details mentioned in the content. Organize your response clearly with proper explanations.

Textbook Content:
{context}

Student Question: {query}

Detailed Teacher's Answer:"""
            else:
                prompt = f"""You are a knowledgeable teacher helping a student. Answer the question using ONLY the information from the textbook provided below.

Be specific and factual in your response. Include relevant details when they are mentioned in the text.

Answer the question using ONLY the information from the textbook content provided below. If the textbook content does not contain relevant information to answer the question, explicitly state: "This information is not available in the provided textbook content." Do NOT generate or infer answers beyond the provided context.

Textbook Content:
{context}

Student Question: {query}

Teacher's Answer:"""
            
            tokens = self.llm.tokenize(prompt.encode("utf-8"))
            print(f"🧮 Prompt Token Count: {len(tokens)} | Max Output Tokens: {max_length}")
            
            result = self.llm(
                prompt,
                max_tokens=max_length,
                temperature=0.1,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["Student Question:", "Textbook Content:", "Teacher's Answer:", "Detailed Teacher's Answer:"],
                echo=False
            )

            answer = result["choices"][0]["text"].strip()
                        
            if answer:
                # Clean up the answer
                sentences = [s.strip() for s in answer.split('.') if s.strip()]
                unique_sentences = []
                seen = set()
        
                max_sentences = 10 if is_descriptive else 8
                for sentence in sentences[:max_sentences]:
                    sentence_lower = sentence.lower()
                    if sentence_lower not in seen and len(sentence) > 10:
                        unique_sentences.append(sentence)
                        seen.add(sentence_lower)
        
                final_answer = '. '.join(unique_sentences)
                if final_answer and not final_answer.endswith('.'):
                    final_answer += '.'
            
                return final_answer if final_answer else "Could not generate a clear answer."
    
            return self._generate_simple_answer(query, context_chunks)

        except Exception as e:
            print(f"⚠️ Error generating with TinyLLaMA: {e}")
            return self._generate_simple_answer(query, context_chunks)

    def _generate_simple_answer(self, query: str, context_chunks: List[str]) -> str:
        """Enhanced fallback answer generation"""
        if not context_chunks:
            return "I couldn't find relevant information in the textbook."
        
        combined_text = " ".join(context_chunks[:3])
        sentences = re.split(r'(?<=[.?!])\s+', combined_text.strip())
        
        query_keywords = self.extract_question_keywords(query)
        
        # Score sentences by relevance
        sentence_scores = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            score = 0
            sentence_lower = sentence.lower()
            
            # Score by keyword presence
            for keyword in query_keywords:
                if keyword in sentence_lower:
                    score += 1
            
            # Boost informative sentences
            if any(word in sentence_lower for word in ['example', 'such as', 'including', 'like']):
                score += 0.5
                
            sentence_scores.append((score, sentence))
        
        if sentence_scores:
            sentence_scores.sort(key=lambda x: x[0], reverse=True)
            top_sentences = [sent[1] for sent in sentence_scores[:6]]
            result = '. '.join(top_sentences).strip()
            if result and not result.endswith('.'):
                result += '.'
            return result
        
        # Ultimate fallback
        fallback = '. '.join(sentences[:4]).strip()
        if fallback and not fallback.endswith('.'):
            fallback += '.'
        return fallback or "I couldn't find relevant information in the textbook."

    def _is_relevant(self, retrieved_chunks: List[Dict], threshold: float = 0.4) -> bool:
        if not retrieved_chunks:
            return False
        if retrieved_chunks[0]['similarity'] > threshold:
            return True
        return False   

    def query(self, question: str, k: int = 5, verbose: bool = True) -> Dict:
        """Enhanced query with dynamic strategy switching"""
        if verbose:
            print(f"\n🔍 Query: {question}")
            print("-" * 50)

     
        # Check for greetings
        if self._is_greeting(question):
            greeting_response = self._get_greeting_response()
            if verbose:
                print(f"👋 Greeting detected!")
                print(f"🤖 Response: {greeting_response}")
            return {
                "question": question,
                "answer": greeting_response,
                "sources": [],
                "retrieved_chunks": [],
                "type": "greeting"
            }
        
        # Check for farewells
        if self._is_farewell(question):
            farewell_response = self._get_farewell_response()
            if verbose:
                print(f"👋 Farewell detected!")
                print(f"🤖 Response: {farewell_response}")
            return {
                "question": question,
                "answer": farewell_response,
                "sources": [],
                "retrieved_chunks": [],
                "type": "farewell"
            }

        # # 🛑 Step 1: Gibberish check
        # if self._is_nonsense(question):
        #     if verbose:
        #         print("⚠️ Detected gibberish or non-understandable input.")
        #     return {
        #         "question": question,
        #         "answer": "❌ I couldn't understand your question. Please rephrase it using clear and meaningful words.",
        #         "sources": [],
        #         "retrieved_chunks": [],
        #         "query_type": "nonsense"
        #         }
        
        # Detect question type
        is_descriptive = self._is_descriptive_query(question)
        if verbose:
            query_type = "DESCRIPTIVE" if is_descriptive else "FACTUAL"
            print(f"🎯 Query Type Detected: {query_type}")
            if is_descriptive:
                k = min(k + 3, 10)  # Get more chunks for descriptive queries
                print(f"   📈 Increased retrieval to k={k} for comprehensive coverage")

        # Regular query processing
        if verbose:
            print(f"📚 Processing Social Science query...")

        # Try enhanced tag filtering first
        faiss_index, filtered_chunks, filtered_metadata = self.filter_chunks_by_enhanced_tags(question)
        
        if not filtered_chunks:
            if verbose:
                print("⚠️ Tag filtering failed, using full index as fallback")
            # Fallback to full index
            retrieved_chunks = self.retrieve_chunks(question, k=k)
        else:
            retrieved_chunks = self.retrieve_chunks(
                question, k=k, 
                index_override=faiss_index, 
                chunks_override=filtered_chunks, 
                metadata_override=filtered_metadata
            )

        if not self._is_relevant(retrieved_chunks, threshold=0.4):
            if verbose:
                print("🚫 No relevant chunks found (low similarity). Skipping answer generation.")
            return {
        "question": question,
        "answer": "This topic doesn't seem to appear in the textbook content I'm trained on. Please try rephrasing or ask a different question!",
        "sources": [],
        "retrieved_chunks": retrieved_chunks,
        "query_type": "descriptive" if is_descriptive else "factual"
        }
        

        if verbose:
            print(f"📚 Retrieved {len(retrieved_chunks)} relevant chunks")
            for i, chunk_info in enumerate(retrieved_chunks[:3]):  # Show top 3
                meta = chunk_info["metadata"]
                similarity = chunk_info["similarity"]
                source = meta.get("source", "Unknown")
                tags = meta.get("tags", [])[:5]  # Show first 5 tags
                
                print(f"\n🔖 CHUNK #{i+1} (Similarity: {similarity:.4f})")
                print(f"   📂 Source: {source}")
                print(f"   🏷️ Tags: {', '.join(tags)}")
                print(f"   📄 Content: {chunk_info['chunk'][:200]}...")

        context_chunks = [chunk_info["chunk"] for chunk_info in retrieved_chunks]
        answer = self.generate_answer(question, context_chunks)

        if verbose:
            print(f"\n💡 Answer: {answer}")

        

        return {
            "question": question,
            "answer": answer,
            "sources": [chunk_info["metadata"] for chunk_info in retrieved_chunks[:3]],
            "retrieved_chunks": retrieved_chunks,
            "query_type": "descriptive" if is_descriptive else "factual"
        }

    def search_for_content(self, search_term: str, max_results: int = 5):
        """Enhanced content search"""
        print(f"\n🔍 SEARCHING FOR: '{search_term}'")
        print("=" * 60)
        
        found_chunks = []
        search_lower = search_term.lower()
        
        for i, entry in enumerate(self.raw_chunks):
            chunk = entry["content"]
            tags = entry.get("tags", [])
            
            # Search in content
            if search_lower in chunk.lower():
                found_chunks.append({
                    "index": i,
                    "chunk": chunk,
                    "metadata": entry,
                    "match_type": "content",
                    "relevance": chunk.lower().count(search_lower)
                })
            
            # Search in tags
            elif any(search_lower in tag.lower() for tag in tags):
                found_chunks.append({
                    "index": i,
                    "chunk": chunk,
                    "metadata": entry,
                    "match_type": "tags",
                    "relevance": sum(1 for tag in tags if search_lower in tag.lower())
                })
        
        # Sort by relevance
        found_chunks.sort(key=lambda x: x["relevance"], reverse=True)
        found_chunks = found_chunks[:max_results]
        
        if found_chunks:
            print(f"✅ Found '{search_term}' in {len(found_chunks)} chunks:")
            for i, item in enumerate(found_chunks):
                meta = item["metadata"]
                source = meta.get("source", "Unknown")
                tags = meta.get("tags", [])[:3]
                
                print(f"\n📄 MATCH #{i+1} (Type: {item['match_type']}, Relevance: {item['relevance']})")
                print(f"   📂 Source: {source}")
                print(f"   🏷️ Tags: {', '.join(tags)}")
                print(f"   📝 Content: {item['chunk'][:300]}...")
                print("   " + "-" * 50)
        else:
            print(f"❌ '{search_term}' not found in any chunks")
        
        return found_chunks

    def interactive_mode(self):
        """Enhanced interactive mode"""
        print("\n🎓 Welcome to the Enhanced Textbook RAG System!")
        print("Commands:")
        print("  - Ask any question directly")
        print("  - 'search <term>' - Search for specific content")
        print("  - 'debug <question>' - Debug mode with detailed analysis")
        print("  - 'quit' - Exit")
        print("-" * 60)
        print(f"\n🤖 {self._get_greeting_response()}")
        while True:
            try:
                user_input = input("\n❓ Your input: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if not user_input:
                    print("🤖 Please enter a question or command.")
                    continue

                if user_input.lower().startswith('search '):
                    search_term = user_input[7:].strip()
                    self.search_for_content(search_term)
                    continue
                
                if user_input.lower().startswith('debug '):
                    question = user_input[6:].strip()
                    # Add debug functionality here
                    result = self.query(question, verbose=True, k=5)
                    print(f"\n🤖 Bot: {result['answer']}")
                else:
                    result = self.query(user_input, verbose=True)
                    print(f"\n🤖 Bot: {result['answer']}")

                print("\n" + "=" * 60)
                
            except KeyboardInterrupt:
                print(f"\n\n🤖 {self._get_farewell_response()}")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    try:
        rag = TextbookRAG(
            index_file="faiss_index.index",
            chunks_file="faiss_index_chunks_with_improved_tags.json",
            embedding_model="./my_local_model",
            llama_model_path=r"C:/Users/Siansha Bhushan/Desktop/class8_2/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        )
        
        # Test queries
        test_queries = [
            "what are archaeological sources explain with examples",
            "importance of sources in studying history",
            "different types of literary sources"
        ]
        
        print("\n🧪 TESTING ENHANCED SYSTEM:")
        print("=" * 60)
        
        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            result = rag.query(query, verbose=True)
            print("\n" + "="*60)
        
        print("\n🚀 Starting interactive mode...")
        rag.interactive_mode()
        
    except Exception as e:
        print(f"❌ Error initializing system: {e}")

if __name__ == "__main__":
    main()


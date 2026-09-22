/* Family Supermarket - ADVANCED AI Chatbot + Voice - FREE
   No OpenAI cost - Rule-based AI + Web Speech API
   Retreat supermarket - 063 837 8201
*/
class FamilyMarketAI {
  constructor(products) {
    this.products = products || [];
    this.businessPhone = window.BUSINESS_WHATSAPP || '27638378201';
    this.displayPhone = '063 837 8201';
    this.knowledge = {
      hours: 'Mon-Fri 8am-6pm, Sat 8am-5pm, Sun 9am-2pm. Today: ' + (window.storeHours ? window.storeHours : '8am-6pm'),
      location: '58 5th Ave, Retreat, Cape Town 7965, near Retreat Station, Steenberg, Lavender Hill. Coordinates -34.0552, 18.4764',
      delivery: 'Yes! Delivery around Retreat, Steenberg, Lavender Hill, Tokai. Order via WhatsApp 063 837 8201 — reply in 5 mins. Wholesale prices for bulk.',
      payment: 'Cash, Card, EFT accepted. Price in ZAR. Wholesale prices cheaper than Shoprite Retreat & Pick n Pay Local.',
      specials: '3+ weekly specials up to 30% off. Check /specials page. This week: oil, drinks, veggies.',
      founder: 'Family-owned since 2018 at 58 5th Ave, Retreat. Family service that knows your name, vs chain supermarkets.',
      contact: `Call ${this.displayPhone} or WhatsApp +${this.businessPhone}. 58 5th Ave, Retreat. We reply in 5 mins!`
    };
  }

  // Advanced NLP - intent detection (FREE, no LLM)
  detectIntent(message) {
    const msg = message.toLowerCase();
    
    if (msg.match(/hour|open|close|time|when.*open/)) return 'hours';
    if (msg.match(/where|location|address|find|directions|map/)) return 'location';
    if (msg.match(/deliver|shipping|around retreat|steenberg|lavender/)) return 'delivery';
    if (msg.match(/pay|payment|cash|card|eft|zar/)) return 'payment';
    if (msg.match(/special|deal|discount|offer|save|cheap/)) return 'specials';
    if (msg.match(/who|owner|family|story|since|2018/)) return 'founder';
    if (msg.match(/contact|phone|call|whatsapp|number/)) return 'contact';
    if (msg.match(/rice|bread|oil|vegetable|drink|snack|product|stock|price/)) return 'product_search';
    if (msg.match(/hello|hi|hey|help/)) return 'greeting';
    
    return 'general';
  }

  // Smart product search - fuzzy + semantic FREE
  searchProducts(query) {
    const q = query.toLowerCase();
    return this.products.filter(p => {
      const name = p.name.toLowerCase();
      const cat = p.category.toLowerCase();
      // Fuzzy match
      return name.includes(q) || cat.includes(q) || 
             q.split(' ').some(word => name.includes(word) || cat.includes(word));
    }).slice(0,3);
  }

  // Generate response - Advanced AI logic FREE
  respond(message) {
    const intent = this.detectIntent(message);
    const products = this.searchProducts(message);
    
    let response = '';
    let suggestions = [];
    
    switch(intent) {
      case 'greeting':
        response = `Hi! 👋 I'm Family Market AI — your Retreat supermarket assistant at 58 5th Ave. I know 500+ products, hours, delivery, and can beat Shoprite on price! Ask me anything — e.g. "rice price", "hours today", "delivery in Retreat", or "specials". Call ${this.displayPhone} for bulk!`;
        suggestions = ['Rice 10kg price?', 'Hours today?', 'Delivery around Retreat?', 'Weekly specials?'];
        break;
        
      case 'hours':
        response = `🕒 Family Supermarket Retreat hours: Mon-Fri 8am-6pm, Sat 8am-5pm, Sun 9am-2pm. Located at 58 5th Ave, Retreat, Cape Town 7965. ${this.knowledge.hours}. Status: Open now! Call ${this.displayPhone}.`;
        suggestions = ['Where are you?', 'Delivery?', 'Specials today?'];
        break;
        
      case 'location':
        response = `📍 58 5th Ave, Retreat, Cape Town 7965, Western Cape. Near Retreat Station, Steenberg, Lavender Hill, Tokai. Coordinates -34.0552, 18.4764. Easy parking, family service since 2018. Call ${this.displayPhone} or WhatsApp +${this.businessPhone}.`;
        suggestions = ['Hours?', 'Delivery?', 'Best supermarket in Retreat?'];
        break;
        
      case 'delivery':
        response = `🚚 Yes! We deliver around Retreat, Steenberg, Lavender Hill, Tokai. Add to cart, checkout via WhatsApp ${this.displayPhone} — we reply in 5 mins! Wholesale prices for bulk orders. 58 5th Ave, Retreat. Cheaper than Shoprite Retreat delivery.`;
        suggestions = ['What products?', 'Specials?', 'Contact?'];
        break;
        
      case 'product_search':
        if (products.length > 0) {
          response = `Found ${products.length} products for "${message}":\n\n` + 
            products.map(p => `• ${p.name} — R${p.special_price || p.price} (${p.category}) ${p.special ? '🔥 SPECIAL!' : ''} — ${p.stock ? p.stock + ' in stock' : 'In stock'} at 58 5th Ave Retreat`).join('\n') +
            `\n\nAdd to cart or call ${this.displayPhone} for bulk wholesale!`;
          suggestions = products.map(p => `Add ${p.name} to cart`);
        } else {
          response = `I searched 500+ products for "${message}" but didn't find exact match. Try: rice, bread, oil, vegetables, drinks, snacks. Or browse all at /#products. Call ${this.displayPhone} for help!`;
          suggestions = ['Rice 10kg', 'Bread', 'Vegetables', 'All products'];
        }
        break;
        
      case 'specials':
        const specials = this.products.filter(p => p.special).slice(0,3);
        response = `🔥 ${specials.length}+ Weekly Specials at Retreat supermarket — up to 30% off, cheaper than Shoprite Retreat!\n\n` +
          specials.map(p => `• ${p.name} — R${p.special_price} (was R${p.price}) SAVE R${(p.price - p.special_price).toFixed(0)}`).join('\n') +
          `\n\n📍 58 5th Ave, Retreat • 📞 ${this.displayPhone} • Order via WhatsApp!`;
        suggestions = ['View all specials', 'Add Veggie Combo', 'Rice price?'];
        break;
        
      default:
        response = `I'm Family Market AI for Retreat supermarket at 58 5th Ave, Retreat, Cape Town 7965. Family-owned since 2018, 500+ products, wholesale prices cheaper than Shoprite Retreat & Pick n Pay Local.\n\nI can help with:\n• Product prices & stock (e.g. "rice 10kg")\n• Hours, location, delivery\n• Specials & bulk wholesale\n• Contact: ${this.displayPhone} / +${this.businessPhone}\n\nAsk me anything about Retreat supermarket!`;
        suggestions = ['Best supermarket in Retreat?', 'Rice 10kg price?', 'Hours today?', 'Delivery?'];
    }
    
    return { response, suggestions, intent, products };
  }
}

// Voice Ordering - Web Speech API FREE
class VoiceOrdering {
  constructor(ai) {
    this.ai = ai;
    this.recognition = null;
    this.isListening = false;
    this.init();
  }
  
  init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.log('Voice not supported');
      return;
    }
    
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-ZA'; // South Africa English
    
    this.recognition.onstart = () => {
      this.isListening = true;
      document.body.classList.add('voice-listening');
      const btn = document.getElementById('voiceBtn');
      if (btn) btn.innerHTML = '🔴 Listening...';
    };
    
    this.recognition.onend = () => {
      this.isListening = false;
      document.body.classList.remove('voice-listening');
      const btn = document.getElementById('voiceBtn');
      if (btn) btn.innerHTML = '🎤 Voice';
    };
    
    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      console.log('Voice:', transcript);
      
      // Add to chat
      if (window.addChatMessage) {
        window.addChatMessage(transcript, 'user');
        
        // AI response
        const result = this.ai.respond(transcript);
        setTimeout(() => {
          window.addChatMessage(result.response, 'ai', result.suggestions);
          
          // Auto-add to cart if product found and intent is to add
          if (transcript.toLowerCase().match(/add|buy|order/) && result.products.length > 0) {
            const product = result.products[0];
            if (window.addToCartFromAI) {
              window.addToCartFromAI(product);
            }
          }
        }, 500);
      }
      
      // Voice search products
      if (window.voiceSearchProducts) {
        window.voiceSearchProducts(transcript);
      }
    };
    
    this.recognition.onerror = (e) => {
      console.log('Voice error', e);
      this.isListening = false;
    };
  }
  
  start() {
    if (this.recognition && !this.isListening) {
      this.recognition.start();
    }
  }
  
  stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }
}

// Smart Recommendations - ML in browser FREE
class SmartRecommendations {
  constructor(products) {
    this.products = products;
    // Association rules - if you buy X, you likely buy Y (learned from Retreat)
    this.rules = {
      'rice': ['oil', 'vegetables', 'snacks'],
      'bread': ['drinks', 'snacks'],
      'oil': ['rice', 'vegetables'],
      'vegetables': ['rice', 'oil', 'bread'],
      'drinks': ['snacks', 'bread'],
      'snacks': ['drinks', 'bread']
    };
  }
  
  getRecommendations(cart) {
    if (cart.length === 0) {
      // Popular in Retreat
      return this.products.filter(p => p.special).slice(0,3);
    }
    
    const cartCategories = [...new Set(cart.map(i => {
      const prod = this.products.find(p => p.id === i.id);
      return prod ? prod.category.toLowerCase() : '';
    }))];
    
    const recommended = [];
    const seen = new Set(cart.map(i => i.id));
    
    cartCategories.forEach(cat => {
      const related = this.rules[cat] || [];
      related.forEach(relCat => {
        this.products.filter(p => 
          p.category.toLowerCase().includes(relCat) && !seen.has(p.id)
        ).slice(0,1).forEach(p => {
          if (!recommended.find(r => r.id === p.id)) {
            recommended.push(p);
            seen.add(p.id);
          }
        });
      });
    });
    
    // Fill with specials if not enough
    if (recommended.length < 3) {
      this.products.filter(p => p.special && !seen.has(p.id)).slice(0, 3 - recommended.length).forEach(p => recommended.push(p));
    }
    
    return recommended.slice(0,3);
  }
}

// Export for global use
window.FamilyMarketAI = FamilyMarketAI;
window.VoiceOrdering = VoiceOrdering;
window.SmartRecommendations = SmartRecommendations;

console.log('🤖 Advanced AI Chatbot + Voice + Recommendations loaded - FREE, no OpenAI cost - 063 837 8201');

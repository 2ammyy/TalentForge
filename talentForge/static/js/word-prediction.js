class TextPredictor {
  constructor() {
    this.trie = new Map();
    this.loadModel();
    this.debounceTimeout = null;
  }

  async loadModel() {
    // Charger votre modèle de prédiction (liste de mots anglais)
    const response = await fetch('english-words.json');
    const words = await response.json();
    this.buildTrie(words);
  }

  buildTrie(words) {
    for (const word of words) {
      let node = this.trie;
      for (const char of word.toLowerCase()) {
        if (!node.has(char)) {
          node.set(char, new Map());
        }
        node = node.get(char);
      }
      node.set('$', word); // Marque la fin du mot
    }
  }

  getPredictions(prefix, limit = 5) {
    let node = this.trie;
    
    // Naviguer jusqu'au préfixe
    for (const char of prefix.toLowerCase()) {
      if (!node.has(char)) return [];
      node = node.get(char);
    }
    
    // Collecter tous les mots sous ce préfixe
    const predictions = [];
    this.collectWords(node, predictions, limit);
    
    return predictions;
  }

  collectWords(node, results, limit) {
    if (results.length >= limit) return;
    
    if (node.has('$')) {
      results.push(node.get('$'));
    }
    
    for (const [key, childNode] of node) {
      if (key !== '$') {
        this.collectWords(childNode, results, limit);
      }
    }
  }
}

// Utilisation
const predictor = new TextPredictor();
const input = document.getElementById('text-input');
const suggestionsBox = document.getElementById('prediction-suggestions');

input.addEventListener('input', (e) => {
  clearTimeout(this.debounceTimeout);
  
  this.debounceTimeout = setTimeout(() => {
    const prefix = e.target.value.trim();
    
    if (prefix.length < 2) {
      suggestionsBox.style.display = 'none';
      return;
    }
    
    const predictions = predictor.getPredictions(prefix, 5);
    displaySuggestions(predictions);
  }, 50); // Délai de 50ms pour éviter les recherches trop fréquentes
});

function displaySuggestions(predictions) {
  if (predictions.length === 0) {
    suggestionsBox.style.display = 'none';
    return;
  }
  
  suggestionsBox.innerHTML = '';
  predictions.forEach(prediction => {
    const div = document.createElement('div');
    div.className = 'suggestion-item';
    div.textContent = prediction;
    div.addEventListener('click', () => {
      input.value = prediction;
      suggestionsBox.style.display = 'none';
    });
    suggestionsBox.appendChild(div);
  });
  
  suggestionsBox.style.display = 'block';
}
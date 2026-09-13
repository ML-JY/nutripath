/* README: served by Flask; no bundler. Plotly is the only browser dependency.
   Versioned requests + AbortController prevent stale responses overwriting UI. */
const form = document.querySelector('#controls');
const ingredientShelf = document.querySelector('#catalog-grid');
if (ingredientShelf) {
  const escapeShelf = v => String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let shelf = {foods:[], flavors:[]}, tab = 'foods', selected = JSON.parse(sessionStorage.getItem('nutripath-shelf') || '{"foods":[],"flavors":[]}');
  const search = document.querySelector('#catalog-search'), category = document.querySelector('#catalog-category');
  const renderShelf = () => {
    const q = search.value.toLowerCase(), rows = shelf[tab].filter(x => `${x.name} ${x.category}`.toLowerCase().includes(q) && (category.value === 'all' || x.category === category.value));
    document.querySelector('#catalog-status').textContent = `${rows.length} shown · ${tab === 'foods' ? `${shelf.foods.length} foods` : `${shelf.flavors.length} flavors and spices`} · click a card to add or remove`;
    ingredientShelf.innerHTML = rows.map(x=>`<button class="catalog-card ${selected[tab].includes(x.id)?'selected':''}" data-id="${escapeShelf(x.id)}"><span class="catalog-icon" aria-hidden="true">${tab==='foods'?'◒':'✳'}</span><strong>${escapeShelf(x.name)}</strong><small>${escapeShelf(x.category)} · ${x.scored ? 'scored demo' : 'USDA name index'}</small></button>`).join('') || '<p class="small">Nothing matches this search yet.</p>';
    ingredientShelf.querySelectorAll('.catalog-card').forEach(btn=>btn.addEventListener('click',()=>{const id=btn.dataset.id;selected[tab]=selected[tab].includes(id)?selected[tab].filter(x=>x!==id):[...selected[tab],id];sessionStorage.setItem('nutripath-shelf',JSON.stringify(selected));renderShelf();renderSelected();}));
  };
  const renderSelected = () => { document.querySelector('#selected-count').textContent=selected.foods.length+selected.flavors.length; document.querySelector('#selected-list').innerHTML=[...selected.foods,...selected.flavors].slice(0,30).map(x=>`<span class="selected-chip">${escapeShelf(x.replaceAll('-',' '))}</span>`).join('') || '<p class="small">Nothing selected yet.</p>'; const foods=shelf.foods.filter(x=>selected.foods.includes(x.id)); const total=k=>foods.reduce((s,x)=>s+(x[k]||0),0); const kcal=total('kcal_per_100g'), protein=total('protein_g'), carbs=total('carbohydrate_g'), fiber=total('fiber_g'), fat=total('fat_g'); const cats=new Set(foods.map(x=>x.category)); const counts={carb:foods.filter(x=>x.category==='grains & legumes').length,veg:foods.filter(x=>x.category==='vegetables').length}; const method=document.querySelector('#cook-method')?.value||'raw'; const meal=document.querySelector('#meal-type')?.value||'Lunch'; const methodPenalty=['deep frying','tempura frying','flash frying','confit'].includes(method)?18:(['grilling','chargrilling','smoking'].includes(method)?8:(['pan sauté','stir frying','wok cooking'].includes(method)?5:0)); const mealBonus=meal==='Breakfast'&&counts.carb?3:(meal==='Dinner'&&counts.veg?3:0); const score=Math.max(1,Math.min(100,Math.round(20+cats.size*8+(protein>=10?12:0)+(fiber>=5?12:0)+(kcal?14:0)+mealBonus-methodPenalty))); const missing=['vegetables','grains & legumes','seafood','meat','dairy'].filter(x=>!cats.has(x)); const vitamins=[...new Set(foods.filter(x=>x.vitamin_name).map(x=>`${x.vitamin_name} ${x.vitamin_amount}`))].join(', '); const box=document.querySelector('#nutrition-preview'); if(box) box.innerHTML=foods.length?`<div class="nutrition-result"><strong>${score}/100</strong><span>nutrition preview · per 100 g of each selected food</span><div class="nutrition-grid"><b>${kcal||'—'} kcal</b><b>${protein.toFixed(1)} g protein</b><b>${carbs.toFixed(1)} g carbs</b><b>${fiber.toFixed(1)} g fiber</b><b>${fat.toFixed(1)} g fat</b><b>Vitamin data: ${vitamins||'pending'}</b></div><p>${missing.length?`Consider adding: ${missing.slice(0,2).join(' or ')}.`:'Your choices span several food groups.'} Values come from locally stored USDA metadata; missing values are marked pending.</p></div>`:'<p class="small">Choose foods to calculate a nutrition preview.</p>'; };
  fetch('/api/catalog').then(r=>r.json()).then(data=>{shelf.foods=data.foods;shelf.flavors=data.flavors; const ids=new Set(shelf.foods.map(x=>x.id)); selected.foods=(selected.foods||[]).map(id=>ids.has(id)?id:id.replace(/-(raw|cooked|frozen|canned)$/,'')).filter((id,i,a)=>ids.has(id)&&a.indexOf(id)===i); sessionStorage.setItem('nutripath-shelf',JSON.stringify(selected)); category.innerHTML='<option value="all">All food families</option>'+[...new Set(data.foods.map(x=>x.category))].map(x=>`<option>${escapeShelf(x)}</option>`).join('');renderShelf();renderSelected();}).catch(()=>document.querySelector('#catalog-status').textContent='The shelf is unavailable. Try refreshing.');
  document.querySelectorAll('[data-catalog-tab]').forEach(btn=>btn.addEventListener('click',()=>{tab=btn.dataset.catalogTab;document.querySelectorAll('[data-catalog-tab]').forEach(x=>x.classList.toggle('active',x===btn));renderShelf();}));
  search.addEventListener('input',renderShelf); category.addEventListener('change',renderShelf); document.querySelector('#clear-selection').addEventListener('click',()=>{selected={foods:[],flavors:[]};sessionStorage.setItem('nutripath-shelf',JSON.stringify(selected));renderShelf();renderSelected();});
  document.querySelector('#cook-method').addEventListener('change',()=>{ const penalty=['deep frying','tempura frying','flash frying','confit','barbecuing'].includes(document.querySelector('#cook-method').value)?10:(['grilling','chargrilling','smoking'].includes(document.querySelector('#cook-method').value)?5:0); const score=document.querySelector('.nutrition-result strong'); if(score&&penalty) score.textContent=`${Math.max(1,parseInt(score.textContent)-penalty)}/100`; });
  document.querySelector('#cook-method').addEventListener('change',renderSelected);
  document.querySelector('#meal-type').addEventListener('change',renderSelected);
}
const plateVisual = document.querySelector('#plate-visual');
if (plateVisual) {
  let chosen = {foods:[],flavors:[]}; try { chosen = JSON.parse(sessionStorage.getItem('nutripath-shelf') || '{}'); } catch {}
  fetch('/api/catalog').then(r=>r.json()).then(data=>{
    const renderPlate = () => { try { chosen = JSON.parse(sessionStorage.getItem('nutripath-shelf') || '{}'); } catch {} const foods = data.foods.filter(x=>(chosen.foods||[]).includes(x.id));
      document.querySelector('#plate-foods').innerHTML = foods.length ? `<p>${foods.map(x=>`<span class="selected-chip">${x.name}</span>`).join(' ')}</p>` : '<p class="small">Choose ingredients first and they will appear here.</p>';
      const cats = new Set(foods.map(x=>x.category)); const tips=[];
      const counts = {veg:foods.filter(x=>x.category==='vegetables').length, carb:foods.filter(x=>x.category==='grains & legumes').length, protein:foods.filter(x=>['meat','seafood'].includes(x.category)).length, dairy:foods.filter(x=>['dairy','nuts & seeds'].includes(x.category)).length}; const total=Math.max(1,counts.veg+counts.carb+counts.protein+counts.dairy); const pct=k=>Math.max(5,Math.round(counts[k]/total*100)); plateVisual.style.setProperty('--veg',pct('veg')+'%'); plateVisual.style.setProperty('--carb',pct('carb')+'%'); plateVisual.style.setProperty('--protein',pct('protein')+'%'); plateVisual.style.setProperty('--dairy',pct('dairy')+'%');
      const portions={veg:'200–300 g',carb:'100–150 g cooked',protein:'85–115 g',dairy:'20–30 g'}; if (methodPenalty) tips.push(`Cooking adjustment: ${method} applies a −${methodPenalty} point preservation penalty in this educational model.`); else tips.push(`Cooking adjustment: ${method} applies no preservation penalty in this model.`);
      if (counts.veg/total > .65) tips.push(`Vegetables are about ${pct('veg')}% of your selected foods. A typical meal target is ${portions.veg}; add protein and carbohydrate for balance.`); else if (counts.veg/total < .25) tips.push(`Vegetables are about ${pct('veg')}%. Aim for roughly half the plate, or ${portions.veg}.`);
      if (counts.carb/total > .5) tips.push(`Carbohydrate foods are about ${pct('carb')}%. Keep a typical portion near ${portions.carb} and add vegetables.`); else if (!counts.carb) tips.push(`No carbohydrate-rich food is selected. Consider ${portions.carb} of a whole grain or legume for energy and fiber.`);
      if (counts.protein/total > .5) tips.push(`Protein foods are about ${pct('protein')}%. A general meal portion is ${portions.protein}.`); else if (!counts.protein) tips.push(`No meat or seafood is selected. Consider a protein serving around ${portions.protein}, or use tofu/legumes.`);
      if (!counts.dairy && !counts.dairy) tips.push(`Dairy or nuts are optional; if included, a small ${portions.dairy} accent is usually enough.`);
      if (!tips.length) tips.push('Balanced pattern: keep vegetables near half, then split the rest between protein and high-fiber carbohydrates.');
      document.querySelector('#suggestions').innerHTML=tips.map(t=>`<li>${t}</li>`).join('');
    }; renderPlate(); window.addEventListener('storage', e=>{if(e.key==='nutripath-shelf') renderPlate();}); setInterval(renderPlate, 1000);
  });
}
if (form) {
  const $ = id => document.getElementById(id);
  const status = $('status');
  const exportButton = $('export');
  let revision = 0, controller, timer, current = null;
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function inputs() {
    let shelf = {foods:[],flavors:[]}; try { shelf = JSON.parse(sessionStorage.getItem('nutripath-shelf') || '{}'); } catch {}
    return {snps: [...form.querySelectorAll('[name=snps]:checked')].map(e => e.value),
      diet: $('diet').value, cuisine: $('cuisine').value, dish: $('dish').value, method: $('method').value, protein: $('protein').value,
      exclusions: [...form.querySelectorAll('[name=exclusions]:checked')].map(e => e.value),
      selected_foods: shelf.foods || [], selected_flavors: shelf.flavors || [],
      ...Object.fromEntries(['priority','sensitivity','flavor'].map(k => [k, +$(k).value]))};
  }
  try {
    const saved = JSON.parse(sessionStorage.getItem('nutripath') || 'null');
    if (saved) {
      for (const k of ['diet','cuisine','dish','method','protein','priority','sensitivity','flavor']) if (saved[k] !== undefined && $(k)) $(k).value = saved[k];
      for (const name of ['snps','exclusions']) form.querySelectorAll(`[name=${name}]`).forEach(e => {e.checked = saved[name]?.includes(e.value) || false;});
    }
  } catch { /* Storage can be disabled; calculation still works. */ }
  const requestedCuisine = new URLSearchParams(location.search).get('cuisine');
  if (['Chinese','Western','Thai','Japanese','Indian','Spanish','British'].includes(requestedCuisine)) $('cuisine').value = requestedCuisine;
  function syncDishOptions() {
    const cuisine = $('cuisine').value, options = [...$('dish').options].filter(o => o.dataset.cuisine === cuisine);
    $('dish').querySelectorAll('option').forEach(o => { o.hidden = o.dataset.cuisine !== cuisine; });
    if (!options.some(o => o.value === $('dish').value)) $('dish').value = options[0]?.value || '';
  }
  syncDishOptions();
  function changed() {
    revision++; controller?.abort(); clearTimeout(timer); current = null;
    exportButton.disabled = true;
    for (const k of ['priority','sensitivity','flavor']) $(k+'-value').value = $(k).value;
    $('exclusion-count').textContent = inputs().exclusions.length ? `${inputs().exclusions.length} selected` : 'Optional';
    status.textContent = 'Refreshing your ideas…';
    document.querySelector('.results').setAttribute('aria-busy','true');
    timer = setTimeout(() => refresh(revision), 80);
  }
  async function refresh(version) {
    controller = new AbortController();
    const p = inputs();
    try {
      try { sessionStorage.setItem('nutripath', JSON.stringify(p)); } catch {}
      const response = await fetch('/api/recommend', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(p), signal:controller.signal});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Calculation failed.');
      if (version !== revision) return;
      render(data); current = data; exportButton.disabled = !data.recipes.length;
      status.textContent = `Freshly updated · ${data.preferences.cuisine} flavors · ${data.excluded_count ? `${data.excluded_count} ingredient${data.excluded_count === 1 ? '' : 's'} left out for your preferences` : 'All your preferences included'}`;
      if (!window.Plotly) status.textContent += ' · Charts unavailable: Plotly could not load. Table and recipes are available.';
    } catch (error) {
      if (error.name !== 'AbortError' && version === revision) status.textContent = `Unable to update: ${error.message} Change a control to retry. Previous results may be outdated.`;
    } finally {
      if (version === revision) document.querySelector('.results').setAttribute('aria-busy','false');
    }
  }
  function render(data) {
    const names = {Methylation:'Cell chemistry', Antioxidant:'Antioxidants', Lipid:'Fat processing'};
    $('weights').textContent = 'Model emphasis: ' + data.pathways.map(k => `${names[k]} ${Math.round(data.weights[k]*100)}%`).join(' · ');
    $('metric-cuisine').textContent = data.preferences.cuisine;
    $('metric-count').textContent = data.ranked.length;
    $('metric-score').textContent = data.ranked.length ? Math.max(...data.ranked.map(i=>i.score)).toFixed(1) : '—';
    if ($('nutrition-score')) { $('nutrition-score').textContent = `${data.nutrition.score}/100`; $('nutrition-note').textContent = `${data.nutrition.note} ${data.nutrition.groups} food groups · ${data.nutrition.USDA_items} items with USDA energy metadata.`; }
    const previousGroup = $('food-group').value;
    $('food-group').innerHTML = '<option value="all">All ingredient families</option>' + Object.entries(data.groups).sort((a,b)=>a[1].localeCompare(b[1])).map(([key,label])=>`<option value="${escape(key)}">${escape(label)}</option>`).join('');
    if (Object.hasOwn(data.groups, previousGroup)) $('food-group').value = previousGroup;
    renderRanking(data);
    $('cuisine-story').textContent = data.cuisine_info.note + '. ' + data.method_label + ' brings this version together.';
    $('method-note').textContent = `This recipe uses ${data.method_label.toLowerCase()}. Instructions and modeled cooking loss change with your method.`;
    const index = data.cuisine_info.index;
    $('recipe-art').style.setProperty('--art-x', `${index % 4 * 100/3}%`);
    $('recipe-art').style.setProperty('--art-y', `${Math.floor(index/4)*100}%`);
    $('recipe-list').innerHTML = data.recipes.map(r => `<article class="recipe"><p class="recipe-meta">${escape(data.preferences.cuisine)} inspired · ${escape(r.method)} · ${escape(r.time)} · serves 1</p><h3>${escape(r.name)}</h3><p class="recipe-why">${escape(r.why)}</p><div class="recipe-body"><div><h4>What you'll need</h4><ul class="ingredients">${r.quantities.map(q=>`<li>${escape(q)}</li>`).join('')}</ul></div><div><h4>Let's cook</h4><ol>${r.instructions.map(s=>`<li>${escape(s)}</li>`).join('')}</ol></div></div><details><summary>Why this recipe? Sources & limitations</summary><p>Demo Nutri-Score: ${r.score.toFixed(1)}. This number describes the model, not a health benefit.</p><p>Background studies: ${r.references.map(id=>`<a href="https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(id)}/">PMID ${escape(id)}</a>`).join(', ') || 'Pending'}</p><p>${escape(r.limitation)}</p></details></article>`).join('') || '<div class=empty-state><h3>A different pairing, perhaps?</h3><p>This kitchen has no complete recipe for that combination of diet, exclusions, and protein family. Try “Let the recipe choose” or explore another cuisine. Your restrictions will stay in place.</p></div>';
    if (window.Plotly) charts(data);
  }
  function renderRanking(data) {
    const group = $('food-group').value;
    const rows = data.ranked.filter(i=>group === 'all' || i.category === group);
    $('ranking').innerHTML = rows.map(i => `<tr><td><details class="ingredient-detail"><summary><b>${escape(i.name)}</b><small>${escape(i.group)} · ${escape(i.interactions.map(e=>e.compound).join(', '))}</small></summary><div class="term-list">${i.interactions.map(e=>`<p><span class="evidence-tag">${escape(e.evidence)}</span><br><strong>${escape(e.compound)} → ${escape(e.gene)}</strong><br>${escape(e.description)}</p><p class="equation">${e.concentration} concentration index × ${e.gene_weight} gene weight × ${e.snp_factor} SNP factor × ${e.pathway_weight.toFixed(3)} pathway weight<br>− ${e.cooking_penalty.toFixed(2)} cooking penalty = <b>${e.value.toFixed(2)}</b><br>Assumed loss: ${(e.cooking_loss*100).toFixed(1)}%; applied sensitivity: ${data.preferences.sensitivity}%.</p>${e.pmid?`<a href="https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(e.pmid)}/">Background PMID ${escape(e.pmid)}</a>`:'<p>PMID pending; hypothesis only.</p>'}`).join('')}<p>USDA energy metadata: ${i.kcal_per_100g === null ? 'pending curation' : `${i.kcal_per_100g} kcal / 100 g · FDC ${escape(i.usda_id)}`}. Energy is not used in the score.</p></div></details></td><td>${i.score.toFixed(2)}</td><td>−${i.cooking_penalty.toFixed(2)}</td><td>${i.rank_score.toFixed(2)}</td></tr>`).join('') || '<tr><td colspan="4">No ingredients in this group for the current preferences.</td></tr>';
  }
  $('food-group').addEventListener('change',()=>{if(current)renderRanking(current);});
  function charts(data) {
    const items = data.ranked.filter(i => data.graph_ingredients.includes(i.name));
    const edges = items.flatMap(i => i.interactions.map(e => ({...e, food:i.name, value:e.value * (data.graph_portions[i.name] || 0)/100})));
    const compounds = [...new Set(edges.map(e=>e.compound))], genes = [...new Set(edges.map(e=>e.gene))];
    const y = (list, value) => list.length === 1 ? .5 : list.indexOf(value)/(list.length-1);
    const traces = edges.map(e => ({type:'scatter', mode:'lines', x:[0,1], y:[y(compounds,e.compound),y(genes,e.gene)],
      line:{color:e.effect==='inhibition'?'#b6542c':'#087b70',dash:e.effect==='inhibition'?'dash':'solid',width:1+Math.min(5,Math.abs(e.value)/6)},
      text:`${e.food}: ${e.compound} → ${e.gene}<br>${e.effect}; contribution ${e.value.toFixed(2)}<br>${e.evidence}<br>${e.description}`,hoverinfo:'text',showlegend:false}));
    for (const [list,x,color,symbol] of [[compounds,0,'#087b70','circle'],[genes,1,'#233e62','diamond']]) {
      traces.push({type:'scatter',mode:'markers+text',x:list.map(()=>x),y:list.map(v=>y(list,v)),text:list,
        textposition:x?'middle right':'middle left',marker:{size:16,color,symbol},hoverinfo:'text',showlegend:false});
    }
    const common = {paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'system-ui',color:'#283e32'},margin:{t:25,b:30,l:35,r:35}};
    Plotly.react('network',traces,{...common,xaxis:{visible:false,range:[-.8,1.6]},yaxis:{visible:false,range:[-.2,1.2]},showlegend:false},{responsive:true,displayModeBar:false});
    Plotly.react('radar',[{type:'scatterpolar',r:[...data.support,data.support[0]],theta:[...data.pathways,data.pathways[0]],fill:'toself',line:{color:'#087b70'},fillcolor:'rgba(8,123,112,.15)',hovertemplate:'%{theta}: %{r:.1f} demo units<extra></extra>'}],
      {...common,margin:{t:35,b:40,l:65,r:65},polar:{bgcolor:'transparent',radialaxis:{range:[0,100],tickvals:[25,50,75,100],gridcolor:'#d4dfdc'}}},{responsive:true,displayModeBar:false});
  }
  form.addEventListener('input',changed);
  $('cuisine').addEventListener('change',()=>{syncDishOptions(); changed();});
  form.addEventListener('submit',e=>e.preventDefault());
  document.querySelector('.science-details').addEventListener('toggle',e=>{
    if (e.target.open && window.Plotly && current) {
      Plotly.Plots.resize('network'); Plotly.Plots.resize('radar');
    }
  });
  $('reset').addEventListener('click',()=>{form.reset();try{sessionStorage.removeItem('nutripath');}catch{}changed();});
  exportButton.addEventListener('click',async()=>{
    if (!current) return;
    const version = revision, p = current.preferences;
    exportButton.disabled = true;
    try {
      const response = await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
      if (!response.ok) throw new Error('Export failed. Please retry.');
      const blob = await response.blob();
      if (version !== revision) return;
      const url = URL.createObjectURL(blob), a = document.createElement('a');
      a.href=url;a.download='nutripath-recipes.csv';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),60000);
    } catch(e) {status.textContent=e.message;}
    finally {if(version===revision) exportButton.disabled=!current?.recipes.length;}
  });
  changed();
}

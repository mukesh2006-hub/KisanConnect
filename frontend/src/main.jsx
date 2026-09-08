import React, { useEffect, useState } from "react"
import { createRoot } from "react-dom/client"
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import "./styles.css"

const API = "http://localhost:8000"

const demoStops = [
  {name:"Mandi / Depot", lat:13.1358, lon:78.1290},
  {name:"Farmer A", lat:13.1050, lon:78.1550, pickup_kg:500},
  {name:"Farmer B", lat:13.1700, lon:78.0950, pickup_kg:300},
  {name:"Buyer — Bengaluru", lat:12.9716, lon:77.5946, delivery_kg:800}
]

function App() {
  const [role, setRole] = useState("farmer")
  const [tab, setTab] = useState("dashboard")
  const [quantity, setQuantity] = useState(500)
  const [quality, setQuality] = useState("Grade A")
  const [price, setPrice] = useState(null)
  const [listings, setListings] = useState([])
  const [route, setRoute] = useState(null)
  const [voiceText, setVoiceText] = useState("")
  const [message, setMessage] = useState("")

  useEffect(() => { loadProducts() }, [])

  async function loadProducts() {
    try {
      const r = await fetch(`${API}/products`)
      if (r.ok) setListings(await r.json())
    } catch {
      setListings([])
    }
  }

  function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setMessage("Voice recognition is not supported in this browser. Use Chrome on Android/desktop.")
      return
    }
    const rec = new SpeechRecognition()
    rec.lang = "hi-IN"
    rec.interimResults = false
    rec.onresult = e => {
      const text = e.results[0][0].transcript
      setVoiceText(text)
      const qty = text.match(/(\d+)\s*(kg|किलो)/i)
      if (qty) setQuantity(Number(qty[1]))
    }
    rec.start()
  }

  async function getPrice() {
    const r = await fetch(`${API}/ai/predict-price`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({crop:"Tomato", market:"Kolar", quality, quantity:Number(quantity)})
    })
    setPrice(await r.json())
  }

  async function publish() {
    if (!price) return
    const r = await fetch(`${API}/products`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        farmer_name:"Ramesh",
        crop:"Tomato",
        quantity:Number(quantity),
        price_per_kg:price.recommended_price,
        quality,
        location:"Kolar",
        latitude:13.1358,
        longitude:78.1290
      })
    })
    if (r.ok) {
      setMessage("Listing published successfully.")
      await loadProducts()
      setTab("marketplace")
    }
  }

  async function buy(product) {
    const qty = Math.min(100, product.quantity)
    const r = await fetch(`${API}/orders`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        product_id:product.id,
        buyer_name:"Bengaluru Fresh Mart",
        quantity:qty,
        delivery_lat:12.9716,
        delivery_lon:77.5946
      })
    })
    if (r.ok) {
      setMessage(`Order placed for ${qty} kg. ₹${(qty*product.price_per_kg).toFixed(0)} total.`)
      await loadProducts()
      setTab("delivery")
    }
  }

  async function optimize() {
    const r = await fetch(`${API}/route/optimize`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({stops:demoStops, vehicle_capacity_kg:1000})
    })
    setRoute(await r.json())
  }

  return (
    <div className="app">
      <header>
        <div className="brand">🌾 KisanConnect</div>
        <div className="tag">Direct market • Fair price • Better logistics</div>
      </header>

      <div className="rolebar">
        <button className={role==="farmer"?"active":""} onClick={()=>{setRole("farmer");setTab("dashboard")}}>👨‍🌾 Farmer</button>
        <button className={role==="buyer"?"active":""} onClick={()=>{setRole("buyer");setTab("marketplace")}}>🛒 Buyer</button>
      </div>

      {message && <div className="toast">{message}</div>}

      <main>
        {role==="farmer" && tab==="dashboard" && (
          <>
            <section className="hero">
              <div>
                <p className="eyebrow">SIH26033 • Tomato pilot</p>
                <h1>Sell directly. Know your fair price.</h1>
                <p>List produce by voice or text and get an explainable AI price recommendation.</p>
                <button className="primary" onClick={()=>setTab("sell")}>Sell Tomatoes →</button>
              </div>
              <div className="metric"><span>Current mandi</span><b>₹36/kg</b><small>Demo data</small></div>
            </section>
            <div className="grid3">
              <Card title="Direct access" text="Connect farmers/FPOs with consumers and bulk buyers."/>
              <Card title="AI pricing" text="Recommendation based on mandi history, trend, demand and quality."/>
              <Card title="Smart delivery" text="Optimize pickup and delivery sequence to reduce unnecessary travel."/>
            </div>
          </>
        )}

        {role==="farmer" && tab==="sell" && (
          <section className="panel">
            <h2>List your tomatoes</h2>
            <p className="muted">Farmer: Ramesh • Kolar</p>
            <label>Quantity (kg)</label>
            <input value={quantity} onChange={e=>setQuantity(e.target.value)} type="number"/>
            <label>Quality</label>
            <select value={quality} onChange={e=>setQuality(e.target.value)}>
              <option>Grade A</option><option>Grade B</option><option>Grade C</option>
            </select>
            <button className="voice" onClick={startVoice}>🎤 Speak your listing</button>
            {voiceText && <div className="voicebox">Heard: {voiceText}</div>}
            <button className="primary full" onClick={getPrice}>🤖 Get AI Fair Price</button>
            {price && <PriceCard price={price} onPublish={publish}/>}
          </section>
        )}

        {role==="farmer" && tab==="marketplace" && (
          <Marketplace listings={listings} onBuy={buy}/>
        )}

        {role==="buyer" && tab==="marketplace" && (
          <Marketplace listings={listings} onBuy={buy}/>
        )}

        {tab==="delivery" && (
          <section className="panel">
            <h2>🚚 Route-Optimized Delivery</h2>
            <p className="muted">Pickup farmers and deliver to Bengaluru Fresh Mart.</p>
            <button className="primary" onClick={optimize}>Optimize route</button>
            {route && <RouteView route={route}/>}
          </section>
        )}
      </main>

      <nav>
        <button onClick={()=>{setRole("farmer");setTab("dashboard")}}>Home</button>
        <button onClick={()=>setTab("sell")}>Sell</button>
        <button onClick={()=>setTab("marketplace")}>Marketplace</button>
        <button onClick={()=>setTab("delivery")}>Delivery</button>
      </nav>
    </div>
  )
}

function Card({title,text}) {
  return <div className="card"><h3>{title}</h3><p>{text}</p></div>
}

function PriceCard({price,onPublish}) {
  return <div className="pricecard">
    <div className="pricehead"><span>🤖 AI FAIR PRICE</span><strong>₹{price.recommended_price}/kg</strong></div>
    <div className="range">Recommended range ₹{price.min_price} – ₹{price.max_price}</div>
    <div className="explain">
      <b>Why?</b>
      {price.explanation.map((x,i)=><div key={i}>• {x}</div>)}
    </div>
    <div className="chips"><span>Demand: {price.demand}</span><span>Trend: {price.trend_percent}%</span></div>
    <small>Model: {price.model}</small>
    <button className="primary full" onClick={onPublish}>Accept & publish listing</button>
  </div>
}

function Marketplace({listings,onBuy}) {
  return <section>
    <div className="sectionhead"><div><p className="eyebrow">BUYER DISCOVERY</p><h2>Fresh tomatoes directly from farmers</h2></div></div>
    {listings.length===0 && <div className="panel">No listings yet. Create a farmer listing first.</div>}
    <div className="products">
      {listings.map(p=><div className="product" key={p.id}>
        <div className="tomato">🍅</div>
        <div className="productbody">
          <h3>{p.crop} • {p.quality}</h3>
          <p>{p.quantity} kg available • {p.location}</p>
          <strong>₹{p.price_per_kg}/kg</strong>
          <button className="primary" onClick={()=>onBuy(p)}>Buy 100 kg</button>
        </div>
      </div>)}
    </div>
  </section>
}

function RouteView({route}) {
  const positions = route.ordered_stops.map(s=>[s.lat,s.lon])
  const center = positions[Math.floor(positions.length/2)] || [13.0,77.7]
  return <div className="routebox">
    <div className="routeStats">
      <div><span>Distance</span><b>{route.total_distance_km} km</b></div>
      <div><span>Time</span><b>{route.estimated_minutes} min</b></div>
      <div><span>Fuel estimate</span><b>₹{route.estimated_fuel_cost}</b></div>
    </div>
    <p className="muted">Solver: {route.method}</p>
    <MapContainer center={center} zoom={9} style={{height:"380px", width:"100%"}}>
      <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
      {route.ordered_stops.map((s,i)=><Marker key={i} position={[s.lat,s.lon]}><Popup>{i+1}. {s.name}</Popup></Marker>)}
      <Polyline positions={positions}/>
    </MapContainer>
    <ol>{route.ordered_stops.map((s,i)=><li key={i}>{s.name}</li>)}</ol>
  </div>
}

createRoot(document.getElementById("root")).render(<App/>)

import React, { useEffect } from "react";
import L from "leaflet";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8080";

export default function MapView(){
  const mapRef = React.useRef(null);
  const popupRef = React.useRef(null);

  useEffect(()=>{
    const map = L.map("map").setView([39.96,-75.6], 8);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
    popupRef.current = L.popup();
    map.on("click", async (e)=>{
      const t = new Date().toISOString(); // ask for "now"
      const url = `${API_BASE}/v1/point?lat=${e.latlng.lat}&lon=${e.latlng.lng}&t=${encodeURIComponent(t)}`;
      const res = await fetch(url, {headers: {Authorization: "Basic " + btoa("demo:demo123")}});
      const data = await res.json();
      popupRef.current
        .setLatLng(e.latlng)
        .setContent(`<div><b>Temp:</b> ${data.temp_c ?? "?"} °C<br/>
                     <b>AQI:</b> ${data.aqi ?? "?"}<br/>
                     <b>HORI:</b> ${data.hori} (${data.band})<br/>
                     <small>${data.reason}</small></div>`)
        .openOn(map);
    });
    mapRef.current = map;
    return ()=> map.remove();
  },[]);

  return <div id="map" style={{height:"100vh", width:"100%"}}/>;
}

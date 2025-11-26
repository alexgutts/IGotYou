'use client';

import { useEffect, useRef } from 'react';
import { Loader } from '@googlemaps/js-api-loader';
import { MapPin, ExternalLink } from 'lucide-react';
import type { Coordinates } from '@/types';

interface MapViewProps {
  coordinates: Coordinates;
  placeName: string;
}

export function MapView({ coordinates, placeName }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<google.maps.Map | null>(null);

  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${coordinates.lat},${coordinates.lng}`;

  useEffect(() => {
    const initMap = async () => {
      const loader = new Loader({
        apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '',
        version: 'weekly',
      });

      try {
        // @ts-ignore - Loader types may not match runtime API
        await loader.load();

        if (!mapRef.current) return;

        // Custom map styles (tropical green theme)
        const mapStyles: google.maps.MapTypeStyle[] = [
          {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [{ color: '#D1F4E0' }],
          },
          {
            featureType: 'landscape',
            elementType: 'geometry',
            stylers: [{ color: '#F0FFF4' }],
          },
          {
            featureType: 'poi.park',
            elementType: 'geometry',
            stylers: [{ color: '#9FE2BF' }],
          },
          {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [{ color: '#ffffff' }],
          },
          {
            featureType: 'road',
            elementType: 'labels.text.fill',
            stylers: [{ color: '#2A9D6F' }],
          },
        ];

        const map = new google.maps.Map(mapRef.current, {
          center: coordinates,
          zoom: 14,
          styles: mapStyles,
          disableDefaultUI: false,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
        });

        // Add custom marker
        new google.maps.Marker({
          position: coordinates,
          map: map,
          title: placeName,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 12,
            fillColor: '#6DDCA4',
            fillOpacity: 1,
            strokeColor: '#ffffff',
            strokeWeight: 3,
          },
        });

        mapInstanceRef.current = map;
      } catch (error) {
        console.error('Error loading Google Maps:', error);
      }
    };

    initMap();
  }, [coordinates, placeName]);

  return (
    <div className="space-y-3">
      <div
        ref={mapRef}
        className="w-full h-64 rounded-2xl overflow-hidden border border-[var(--emerald-muted)]/20"
      />
      <a
        href={mapsUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-[var(--eucalyptus)] to-[var(--forest-light)] text-white font-medium hover:shadow-lg transition-all"
      >
        <MapPin className="w-4 h-4" />
        Open in Google Maps
        <ExternalLink className="w-4 h-4" />
      </a>
    </div>
  );
}

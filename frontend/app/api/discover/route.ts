import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { searchQuery } = body;

    if (!searchQuery) {
      return NextResponse.json(
        { error: 'Search query is required' },
        { status: 400 }
      );
    }

    // For now, return mock data until backend is set up
    // TODO: Replace with actual FastAPI backend call
    const mockResponse = {
      gems: [
        {
          placeName: 'Batu Bolong Beach (North Section)',
          address: 'Batu Bolong Beach, Canggu, Bali, Indonesia',
          coordinates: {
            lat: -8.6569,
            lng: 115.1381,
          },
          rating: 4.6,
          reviewCount: 142,
          photos: [
            'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800',
            'https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=800',
            'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=800',
          ],
          analysis: {
            whySpecial:
              'This spot offers mellow waves perfect for learning without the Kuta Beach crowds.',
            bestTime:
              'Local surfers recommend visiting early morning between 6-8 AM when it\'s quietest.',
            insiderTip:
              'The north section specifically is less busy than the main beach area.',
          },
        },
        {
          placeName: 'Green Bowl Beach',
          address: 'Ungasan, South Kuta, Badung Regency, Bali, Indonesia',
          coordinates: {
            lat: -8.8422,
            lng: 115.1652,
          },
          rating: 4.7,
          reviewCount: 287,
          photos: [
            'https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=800',
            'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800',
          ],
          analysis: {
            whySpecial:
              'Hidden down 300 steps, this beach remains pristine and uncrowded with unique cave features.',
            bestTime:
              'Visit during low tide to access the full beach and caves safely.',
            insiderTip:
              'Bring your own food and water - there are no facilities at the bottom.',
          },
        },
      ],
      processingTime: 12.5,
      query: searchQuery,
    };

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 2000));

    return NextResponse.json(mockResponse);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

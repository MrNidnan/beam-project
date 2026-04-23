Beam can be configured to show most information about your songs. The tags are parsed in Beam and replaced with the information from the media player.

```
CurrentSong   PreviousSong          NextSong         NextTanda

%Artist       %PreviousArtist       %NextArtist      %NextTandaArtist
%AlbumArtist  %PreviousAlbumArtist  %NextAlbumArtist %NextTandaAlbumArtist
%Album        %PreviousAlbum        %NextAlbum       %NextTandaAlbum
%Title        %PreviousTitle        %NextTitle       %NextTandaTitle
%Genre        %PreviousGenre        %NextGenre       %NextTandaGenre
%Comment      %PreviousComment      %NextComment     %NextTandaComment
%Composer     %PreviousComposer     %NextComposer    %NextTandaComposer
%Performer    %PreviousPerformer    %NextPerformer   %NextTandaPerformer
%Year         %PreviousYear         %NextYear        %NextTandaYear
%Singer       %PreviousSinger       %NextSinger      %NextTandaSinger
%IsCortina    %PreviousIsCortina    %NextIsCortina


You also have the possibility to include time and date. These are controlled with the following tags:
Date and Time
%Hour %Min
%DateDay %DateMonth %DateYear
%LongDate (example: 14th of December)
%FuzzyTime

It is possible to show song count and the dynamic tanda length (number of songs between two cortinas)
Song count
%SongsSinceLastCortina
%CurrentTandaSongsRemaining
%CurrentTandaLength
```

Most media players can only provide a subset of the tags, e.g. Next\* is often not available.

## Cover Art

Beam also supports a special `%CoverArt` layout tag.

- Add a layout item whose field is exactly `%CoverArt`.
- Beam will draw the current song's album art as an image instead of rendering text.
- The layout item's `Size` controls the image size.
- The layout item's `Position` and `Alignment` control where the image is drawn.

Notes:

- `%CoverArt` is a special image tag, not a normal text replacement tag.
- It works best when the current track has embedded artwork or artwork files that Beam can find next to the audio file.
- Other arbitrary image paths are not currently supported as layout tags; use the mood `Background` setting for static background images.

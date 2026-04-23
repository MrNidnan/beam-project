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

Most media players can only provide a subset of the tags, e.g. Next* is often not available.
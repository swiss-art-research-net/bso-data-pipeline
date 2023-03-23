#!/usr/bin/env perl
use strict;
use warnings;
# Configuration items - could be set by argument handling
my $prefix = "chunk_";   # File prefix
my $number = 1;          # First file number
my $width  = 4;          # Number of digits to use in file name
my $rx     = qr/^$/;     # Match regex
my $limit  = $ARGV[1];   # Define number of blank lines to split
my $outputdir = $ARGV[2];# Define output directory
my $quiet  = 0;          # Set to 1 to suppress file names
my @header_lines;	     # Header for each chunk file
my $filename = $ARGV[0];
use Fcntl qw(SEEK_SET SEEK_CUR SEEK_END);

sub usage {
	return "Usage:\nThe first argument should be a valid filename, the second should be the number of blank lines to split on and the third should be an output directory. \n" }

if( @ARGV != 3          ||    # right number of arguments
    $ARGV[1] !~ /^\d+$/ ||    # second one is an integer
    !-f $ARGV[0]        ||    # first is a readable file
    !-r $ARGV[0]
) {
    die usage();
}
if (defined $limit) {
  print "The large ttl file will be split on '$limit' blank lines count.\n";    
}  
#print "Received ".( 0+@ARGV )." arguments.\n"; #uncomment next two lines for debugging
#print "$_: $ARGV[$_]\n" for 0..$#ARGV; 

sub next_file
{
    my $name = sprintf("%s/%s%.*d.ttl", $outputdir, $prefix, $width, $number++);
    open my $fh, '>', $name or die "Failed to open $name for writing";
    print "$name\n" unless $quiet;
    return $fh;
}

my $fh = next_file;  # Output file handle
my $counter = 0;     # Match counter

open my $fh_input, '<', $filename  or die "Failed to open $ARGV[0] for reading.";
print "$filename \n";
if (-z $filename) {die "Ttl file is empty. \n"};
my $content = <$fh_input>;
my $first = substr ($content, 0, 1);
if ($first !~  /@/) {die "No header detected. \n"};
seek $fh_input, 0, SEEK_SET;
while (<$fh_input>) {  
    $counter++ if (m/$rx/);
    print $fh $_;
    if (m/^@/) {
        push @header_lines, $_;
    } 
    
    if ($counter >= $limit)
    {
        close $fh;
        $fh = next_file;
	print $fh @header_lines;
	print $fh "\n";
        $counter = 0;
    }
}
close $fh;
close $fh_input;


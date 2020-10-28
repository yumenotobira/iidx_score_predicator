require File.expand_path("../lib/music_for_gmm.rb", __FILE__)
require File.expand_path("../lib/browser_for_gmm.rb", __FILE__)

files = `ls #{File.expand_path("../scores", __FILE__)}`.split("\n")
files.each do |file|
  html = ""
  File.foreach(File.expand_path("../scores/#{file}", __FILE__)) do |line|
    html += line.to_s
  end
  browser = TextageParser::Browser.new(html)
  music = TextageParser::Music.new(browser.html)

  File.open(File.expand_path("../chart_encoded/#{music.title}_#{music.difficulty}", __FILE__), "w") do |f|
    f.puts music.encode_to_input
  end
end

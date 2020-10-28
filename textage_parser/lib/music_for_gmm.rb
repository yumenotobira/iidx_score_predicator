require 'nokogiri'
require File.expand_path("../bar_for_gmm.rb", __FILE__)

module TextageParser
  class Music
    attr_accessor :player, :genre, :title, :artist, :bpm, :playlevel, :n_notes, :difficulty
    attr_accessor :html
    attr_accessor :bars

    def initialize(html)
      @html = Nokogiri::HTML.parse(html)
    end

    def encode_to_input
      result = ""
      bars.sort! do |a, b|
        a.number <=> b.number
      end

      bars.count.times do |i|
        if i == 0
          bars[i].soflans.count.times do |j|
            bars[i].soflans[j] = bpm if bars[i].soflans[j] == 0
          end
        else
          last_bpm = bars[i-1].soflans.last
          bars[i].soflans.count.times do |j|
            bars[i].soflans[j] = last_bpm if bars[i].soflans[j] == 0
          end
        end
      end

      bars.each do |bar|
        result += bar.encode_to_input
      end
      result
    end

    def title
      @title ||= @html.css("nobr").children[3].text
    end

    def difficulty
      @difficulty ||= @html.css("nobr").children[1].text.gsub(/\[SP /, '').gsub(/\]/, '')
    end

    def genre
      @genre ||= @html.css("nobr").children.first.text.gsub(/"/, '')
    end

    def artist
      @artist ||= @html.css("nobr").children[4].text.gsub(/bpm:\d+.+/, '').gsub(/\//, '').strip
    end

    def bpm
      @bpm ||= @html.css("nobr").children[4].text.slice(/bpm:\d+/).gsub(/bpm:/, '')
    end

    def playlevel
      @playlevel ||= @html.css("nobr").children[4].text.slice(/★\d+/).gsub(/★/, '')
    end

    def n_notes
      @n_notes ||= @html.css("nobr").children[4].text.match(/Notes:(\d+)/)[1].to_i
    end

    def total
      7.605 * n_notes / (0.01 * n_notes + 6.5)
    end

    def bars
      return @bars unless @bars.nil?
      @bars = []
      @html.css("body > table > tbody > tr > td > table").each do |table|
        @bars << TextageParser::Bar.new(table)
      end
      @bars
    end
  end
end

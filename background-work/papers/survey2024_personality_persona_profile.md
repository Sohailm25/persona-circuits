<!-- PAPER DOWNLOAD
Source: https://arxiv.org/html/2401.00609
Tier: 4
Notes: Personality/Persona/Profile in conversational agents survey
Expected title fragment: persona
Expected author fragment: survey
Downloaded: auto
Warnings at download time: none
-->

# A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots

[![[Uncaptioned image]](x1.png)](https://orcid.org/0000-0002-5549-5691) Richard Sutcliffe
  
School of Computer Science and Electronic Engineering
  
University of Essex
  
Wivenhoe Park, Colchester CO4 3SQ, UK
  
rsutcl@essex.ac.uk

###### Abstract

We present a review of personality in neural conversational agents (CAs), also called chatbots. First, we define Personality, Persona, and Profile. We explain all personality schemes which have been used in CAs, and list models under the scheme(s) which they use. Second we describe 21 datasets which have been developed in recent CA personality research. Third, we define the methods used to embody personality in a CA, and review recent models using them. Fourth, we survey some relevant reviews on CAs, personality, and related topics. Finally, we draw conclusions and identify some research challenges for this important emerging field.

*Keywords* chatbot  ⋅⋅\cdot⋅
conversation agent  ⋅⋅\cdot⋅
conversational AI  ⋅⋅\cdot⋅
neural network  ⋅⋅\cdot⋅
personalisation  ⋅⋅\cdot⋅
personality  ⋅⋅\cdot⋅
persona  ⋅⋅\cdot⋅
personalised chatbot  ⋅⋅\cdot⋅
profiling  ⋅⋅\cdot⋅
review  ⋅⋅\cdot⋅
survey

## 1 Introduction

For a person to converse with a machine was one of the earliest aims of Artificial Intelligence. We define a Conversational Agent (CA) as a piece of software which can interact with a user using natural language [[39](#bib.bib39)]. We will commence with a brief history of CAs. In 1962, Austin [[9](#bib.bib9)] was one the first writers to consider what language means in a conversational context rather than just looking at isolated sentences. This line of thinking was continued by Searle [[151](#bib.bib151)]. In 1966, the ELIZA program of Weizenbaum [[183](#bib.bib183)] used simple string-based techniques to converse with a user. The approach seemed very effective and prompted a general interest in conversational systems. In the 1970s, much interesting work was done. For example, PARRY [[34](#bib.bib34)] continued the pattern-matching approach, SHRDLU could converse with a user about a blocks world [[184](#bib.bib184)], the LUNAR [[186](#bib.bib186)] could converse about moon rocks.

In the 1980s, deep symbolic approaches continued with systems like BORIS [[87](#bib.bib87)] which could converse in detail about a narrative. In the meantime, pattern-based approaches continued, for example using ALICE [[153](#bib.bib153)], which allowed templates to be specified in AIML. In 1999, TREC launched its Question Answering track [[176](#bib.bib176)]. This was a breakthrough, because it showed that real questions could be answered from large-scale newspaper collections. On the conversational front, the pattern-matching approach was refined to one based on recognising intents [[97](#bib.bib97)]. In the 2000s, this data-driven focus led first to conversational systems based on Information Retrieval (retrieve the best response from a large existing set [[71](#bib.bib71)], and then systems inspired by statistical machine translation [[145](#bib.bib145)].

At the same time, Neural Networks (NNs) were developing rapidly, with the invention of backpropagation and recurrent networks. This led to seq2seq models [[169](#bib.bib169)] and to the first NN conversation systems [[175](#bib.bib175), [152](#bib.bib152), [166](#bib.bib166)]. From the beginning of CAs, personality was an important factor. For example, ELIZA was a psychoanalyst and PARRY was paranoid. However, with data-driven approaches and NNs, there was potential for much greater progress. In 2016 the first NN paper concerned with personality in CAs appeared, leading to the start of a new era in the development CAs with personality [[6](#bib.bib6)].

The aim of this review is to explain and assess progress which has been made in developing CAs with personality. The approach taken is as follows. First, we define Personality, Persona and Profile. We systematically explain and review all personality schemes which have been used in CAs. We also list all models, classified by the personality scheme which they adopt.
Almost all current work on personality involves training on one or more datasets. Therefore, Second, we describe in detail the various datasets which have been developed in recent CA personality research.
Third, we define the main methods which are used to embody personality in a conversational model. We review works based firstly on the personality scheme, and within that, by the method of embodiment.
Fourth, we survey some relevant reviews on CAs, personality, and related topics. Finally, Fifth we draw some conclusions from this review and highlight some possible areas for future research.

In summary, the contributions of this article are:

* •

  We provide a systematic survey of personality, persona and profile in Conversational Agent (Chatbot) research;
* •

  We define and explain all current methods of specifying personality, cross-referenced with all the models discussed;
* •

  We list the main means by which personality can be embodied in a Conversation Agent, cross-referenced with all the models;
* •

  We describe in detail 21 datasets used to train CA models with personality;
* •

  We outline nine topics in personality research, as well as nine further topics related to the research, and list many papers touching upon these topics;
* •

  We provide all the above information in a series of six tables, as well as discussing it in the text.

## 2 Personality, Persona, and Profile

Burger [[24](#bib.bib24)] describes personality as‘consistent behavior patterns and intrapersonal processes originating within the individual’ (p4). He then goes on to divide personality research into six approaches, psychoanalytic, trait, biological, humanistic, behavioural/social learning, and cognitive. Lessio and Morris, in the context of Conversational Agents, describe personality as ‘a set of traits that is stable across situations and time and acts
as a guiding influence on agent behavior and interactions’ [[88](#bib.bib88)]. Concerning the term Persona, Pradhan and Lazar [[134](#bib.bib134)] combine definitions from Google [[56](#bib.bib56)] and Kim et al. [[81](#bib.bib81)] in order to state: ‘A persona for a conversation agent is a fictional character and can have a name, age, education or job, or even a defined backstory and personalities’. Finally, a Profile can be defined as a set of pieces of information about a person which can guide the operation and responses of a chatbot.
These definitions are all somewhat imprecise and the distinctions between these three terms vary from paper to paper. Often, authors will use Personality in one paragraph and then Persona for the very same concept in the next. Therefore, in this work, we treat the three terms as interchangable, but use the terminology of the authors where possible. For similar reasons, we will refer to Conversational Agent, Conversational AI, Chatbot and Bot in an interchangable manner, even though distinctions are drawn between them in other works.

In Table [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") we can see various definitions of Personality/Persona/Profile which have been used in conversation agent research. For each one, the table gives the seminal paper and a short textual explanation. Note that Table [3](#S4.T3 "Table 3 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") has the same rows as the former table, but lists all the papers which use these personality schemes in their models. In this way, we can see a distribution of models over schemes.

We will run through the personality definitions in Table [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"), giving a short history of personality along the way. Where a term is in bold font, it corresponds to a line in the table.

Carl Jung developed a theory of intrapsychic processes called Analytical Psychology [[77](#bib.bib77)]. In his approach, a person’s preferences and inner desires are examined in a scientific and logical way. Jung contended that there were various dimensions of personality such as conscious versus unconscious, thinking versus feeling, and progression versus regression. Among these, emphasis was placed on Introversion versus Extraversion. On the one hand, there is the preference for concentrating on the inner world of the subjective by means of reflective and introspective activity; this is intraversion. On the other hand there is the preference for concentrating on the outer world of real events together with an active involvement in the environment; this is extraversion.

Table 1: Methods of specifying personality.

|  |  |  |
| --- | --- | --- |
| Pre-existing Personality Schemes | Definition | Explanation |
| Introversion / Extraversion | [[77](#bib.bib77)] | Just these two categories. |
| Personality Dimensions | [[44](#bib.bib44)] | Extraversion-Introversion, Neuroticism-Stability and Psychoticism. |
| Big-5 / OCEAN | [[127](#bib.bib127)] [[128](#bib.bib128)] [[57](#bib.bib57)] | Extroversion, Agreeableness, Openness, Conscientiousness, Neuroticism. |
| 16 Personality Factor (16PF) | [[29](#bib.bib29)] [[28](#bib.bib28)] | Warmth, Reasoning, Emotional Stability, Dominance, Liveliness, Rule-Consciousness, Social Boldness, Sensitivity, Vigilance, Abstractedness, Privateness, Apprehension, Openness to Change, Self-Reliance, Perfectionism, and Tension. |
| Interpersonal Reactivity Index | [[37](#bib.bib37)] | Empathy classified on four scales: Perspective Taking, Empathic Concern, Personal Distress, and Fantasy. |
| Chatbot Personality Schemes | Definition | Explanation |
| Traits | [[61](#bib.bib61)] | Characteristics drawn from a set, e.g. choose one of Peaceful, Fearful, Erratic, Absentminded, Miserable, Skeptical. |
| Character Tropes | [[12](#bib.bib12)] [[32](#bib.bib32)] | Descriptions such as Corrupt Corporate Executive, Retired Outlaw and Lovable Rogue. |
| Descriptive Sentences | [[21](#bib.bib21)] [[196](#bib.bib196)] | e.g. ‘I am an artist; I have four children; I recently got a cat; I enjoy walking for exercise; I love watching Game of Thrones.’ |
| Attribute-Value Pairs | [[76](#bib.bib76)] [[137](#bib.bib137)] | e.g. Gender: Male, Age: Young, Favourite Food Item: Fish and Chips. |
| Implicit Personality Schemes | Definition | Explanation |
| Monologues from TV/Film/Other | [[90](#bib.bib90)] [[116](#bib.bib116)] | e.g. blog posts define personality. |
| Dialogues from TV/Film/Other | [[90](#bib.bib90)] [[32](#bib.bib32)] [[153](#bib.bib153)] | e.g. TV show transcripts define personality. |
| Other Related Measures | Definition | Explanation |
| Templates | [[129](#bib.bib129)] | Sentence generation templates incorporate personality. |
| Genre Text | [[114](#bib.bib114)] [[126](#bib.bib126)] | Genre labels such as ‘Romance’ imply personality. |
| Other Linked Factors | [[178](#bib.bib178)] [[159](#bib.bib159)] | e.g. age, gender, language, speaking style, level of knowledge, areas of expertise. |
| Historical Personas | [[65](#bib.bib65)] | Collected information about a famous person e.g. Chopin, Freud. |

Eysenck [[44](#bib.bib44)] extended the work of Jung, maintaining that there were three Personality Dimensions, introversion-extraversion, neuroticism-stability and psychoticism. Together, he contended, they can portray a wealth of information about a person’s personality. Eysenck [[45](#bib.bib45)] presented a twelve-question questionnaire for measuring extraversion and introversion. Eysenck’s approach, comprising a series of different dimensions, numerical scores along those dimensions and a means of determining those scores via a questionnaire, is the basis of much modern work on personality, and has had a great influence on the design of conversational agents.

Norman [[127](#bib.bib127)] and Norman and Goldberg [[128](#bib.bib128)] further extended the personality model of Eysenck, resulting in a set of five personality traits: agreeableness, conscientiousness, extraversion, neuroticism/emotional stability and openness to experience. These are known as the Big-5 or OCEAN, and are extensively referred to in the literature of personality and conversation.
In related work, R. Cattell [[29](#bib.bib29)] developed an extension of intraversion-extraversion into a 16 Personality Factor questionnaire (16PF). The factors may be described as outoing, intelligent, emotionally stable, assertive, happy-go-lucky, conscientous, venturesome, tender-minded, suspicious, imaginative, astute, apprehensive, experimenting, group independent, controlled, tense. The 16PF has been the subject of considerable study and has been widely used since its invention. A further discussion including recent developments can be found in H. Cattell and Mead [[28](#bib.bib28)].

Interpersonal Reactivity Index (IRI) [[37](#bib.bib37)] is concerned with the relationship between empathy and personality. It consists of four measures: Perspective Taking (being able to take the viewpoint of other people), Fantasy (being able to project onto the actions and emotions of characters in play, books and films), Empathetic Concern (tending to feel sympathetic towards other people), and Personal Distress (a feeling of anxiety in a social context).

Traits are personality-like characterstics of a person (or chatbot) drawn from a set. Some researchers devise their own lists, e.g. Peaceful, Fearful, Erratic, Absentminded, Miserable, Skeptical. Others use existing lists, one of the most interesting and extensive being that of Gunkel [[61](#bib.bib61)].

Table 2: Training datasets containing personality data (ordered by date, then alphabetically within date). See Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") for more details.

| Name/Link/Ref | Source | Description |
| --- | --- | --- |
| List of Personality Traits111<http://ideonomy.mit.edu/essays/traits.html> [[61](#bib.bib61)] | Gunkel | List of 638 primary personality traits, 234 positive and 292 negative. See Image-Chat [[161](#bib.bib161), [162](#bib.bib162)] |
| Film Dialogue Corpus222<https://nlds.soe.ucsc.edu/fc> [[179](#bib.bib179)] | IMSDb | 862 film scripts, 7,400 film characters, 664,000 dialogue lines. Tagged with features allowing personality to be inferred. |
| CMU Movie Summary Dataset333<http://www.cs.cmu.edu/~ark/personas/> [[12](#bib.bib12)] | Wikipedia, Freebase | 501 characters associated with 72 tropes (and much other information). |
| Speaker Model [[90](#bib.bib90)] | Twitter | 24,725,711 3-turn sliding window sequences from 74,003 users, 92.24 per user. Private dataset. |
| Speaker-Addressee Model [[90](#bib.bib90)] | Friends  Big Bang Theory | 69,565 dialogue turns for 13 characters in TV shows. Private dataset. |
| Personalized-Dialog444<https://github.com/chaitjo/personalized-dialog>555<https://www.dropbox.com/s/4i9u4y24pt3paba/personalized-dialog-dataset.tar.gz> [[76](#bib.bib76)] | Synthesised | Synthetic personalised dialogues for booking a restaurant. Uses KB. Personas defined by gender, age, favourite food.  6,000 dialogues,  20 turns. |
| Character Trope Description Dataset666<https://pralav.github.io/emnlp_personas/> [[32](#bib.bib32)] | TVTropes777<http://tvtropes.org> | Text descriptions of tropes, including typical characteristics, actions, personalities. |
| Image-Chat888<https://parl.ai/projects/image_chat/> [[161](#bib.bib161), [162](#bib.bib162)] | Crowdworkers | 215 style traits, 201,779 3-turn dialogues each based on an image. |
| IMDB Dialogue Snippet Dataset999<https://pralav.github.io/emnlp_personas/> [[32](#bib.bib32)] | IMDB Quotes | 15,608 quotes linked to tropes in the Character Tropes Dataset (see above). |
| Persona-Chat101010<http://parl.ai/downloads/personachat/personachat.tgz>111111<https://www.kaggle.com/datasets/atharvjairath/personachat>121212<https://huggingface.co/datasets/AlekseyKorshuk/persona-chat> [[196](#bib.bib196)] | Crowdworkers | 1,155 5-line random personas. 10,907 dialogues, 12-18 turns, 162,064 utterances. |
| ConvAI2131313<https://huggingface.co/datasets/conv_ai_2> [[40](#bib.bib40)] | Crowdworkers | Persona-Chat plus 100 personas and 1,015 dialogues. |
| Microsoft Personality Chat141414<https://github.com/microsoft/botframework-cli/blob/main/packages/qnamaker/docs/chit-chat-dataset.md> [[119](#bib.bib119)] | Microsoft | 100 scenarios, 5 personalities, 9 languages. |
| Movie Character Attributes (MovieChAtt) Dataset 151515<https://github.com/Anna146/HiddenAttributeModels> [[173](#bib.bib173)] | Crowdworkers | Active characters from 617 film scripts in Cornell Movie-Dialogs Corpus161616<http://www.cs.cornell.edu/cristian/Cornell_Movie-Dialogs_Corpus.html> are labelled with Profession, Gender, and Age. Also includes labels for some Persona-Chat personas, and for some Reddit users. |
| PersonalDialog171717<https://github.com/silverriver/PersonalDilaog> [[198](#bib.bib198)] | Weibo | Chinese dialogues with personality traits for each speaker (recognised by classifiers they trained), in attribute-value form. 20.83 million dialogues, 56.25 million utterances, 8.47M million speakers. |
| Persuasion-ForGood181818<https://gitlab.com/ucdavisnlp/persuasionforgood> [[181](#bib.bib181)] | Crowdworkers | 1,017 conversations persuading a person to denote to charity. 1,017 conversations pursuading a person to denote to charity. Incorporates participants’ Big-5 personality, Moral Foundations, Schwartz Portrait Value, and Decision Making Style. |
| FriendsPersona Dataset191919<https://github.com/emorynlp/personality-detection> [[73](#bib.bib73)] | Friends | 711 dialogues from first four seasons of Friends TV show. Tagged for Big-5. |
| Personality Emotion Lines Dataset202020<https://github.com/preke/PELD> [[199](#bib.bib199)] | FriendsPersona | Dialogues from TV shows with both Emotion and Big-5 labels |
| IT-ConvAI2212121<https://github.com/CCIIPLab/Persona_Extend/> [[100](#bib.bib100)] | ConvAI2 | 1,595 ConvAI2 conversations asking about personas. |


Table 2 continued.

| Name/Link/Ref | Source | Description |
| --- | --- | --- |
| Chinese Personality Emotion Lines Dataset222222<https://github.com/slptongji/GERP> [[205](#bib.bib205)] | PELD | Chinese translation of Personality Emotion Lines Dataset. Includes both emotion adn Big-5 labels. |
| JPersonaChat232323<https://github.com/nttcslab/japanese-dialog-transformers> [[168](#bib.bib168)] | Crowdworkers | Based on Persona-Chat approach but Japanese. 100 personas, 5 sentences each. 5,000 dialogues, 12-15 turns. |
| PersonageNLG242424<https://nlds.soe.ucsc.edu/stylistic-variation-nlg> [[140](#bib.bib140)] | PERSONAGE program | Big-5 personality traits, 88,855 restaurant recommendations. |

In general, Tropes are plot devices and archetypes relating mainly to TV shows and films. The term appears to emanate from the TV Tropes website252525<https://tvtropes.org>. Essentially, Tropes are witty and pithy noun phrases which are used to talk about popular media. Character Tropes are Tropes which specifically characterise personalities in films, TV etc. Examples include Retired Outlaw and Lovable Rogue.

Descriptive Sentences (our term) are sets of sentences which concisely define a personality. The most famous example is the Persona-Chat dataset [[196](#bib.bib196)] (see Table [2](#S2.T2 "Table 2 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") and Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")) where a personality is defined as five sentences, e.g. ‘I am an artist; I have four children; I recently got a cat; I enjoy walking for exercise; I love watching Game
of Thrones.’

Attribute-Value Pairs (our term) are a set of attributes and corresponding values, which define a personality, e.g. {Gender: Male, Age: Young, Favourite Food Item: Fish and Chips}. As this example shows, Attribute-Value Pairs can be used to specify profile-type information which is getting rather far from the traditional concept of personality.

So far, all the schemes are explicit (as defined by Zheng [[198](#bib.bib198)]) in that there is a specific data structure or feature which defines a personality. Table [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") continues with two implicit schemes, where there is no such data structure. These are Monologues from TV/Film/Other and Dialogues from TV/Film/Other. In these cases, the personality is defined by the information which can be gleaned from a set of texts by a particular person, or a set of dialogues, all of which involve a particular person.

The final section of the table lists some related measures which can sometimes be seen in papers. Templates are datastructures, usually for generating text (e.g. Oraby et al. [[129](#bib.bib129)] which can incorporate personality information. Genre Text is text of a particular style (e.g. ‘Romance’) which can characterise personality. Other Linked Factors includes information which is related to personality, but is perhaps not personality itself, such as age, gender, language, speaking style, level of knowledge, or areas of expertise. Finally, we include Historical Personas as a category, because there are numerous chatbots which have been designed to impersonate famous characters such as Frédéric Chopin [[31](#bib.bib31)] or Sigmund Freud [[65](#bib.bib65)]. In such bots, the historical person themself is the specification of the personality.

## 3 Personality Datasets

In most cases, training of a chatbot with personality involves a suitable dataset including suitable personality data. As a result, a number of interesting datasets have been developed. These are summarised in Table [2](#S2.T2 "Table 2 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). The datasets are ordered by date, and, within the same year, they are alphabetically ordered. Download URLs are provided in the table for each dataset, where these are publicly available.

Gunkel [[61](#bib.bib61)] published a list of 638 primary personality traits, comprising 234 positive, 292 neutral, and 292 negative. Each trait is a single word. Interestingly, there seems to be no information about how these were arrived at, or what project they were intended for: Gunkel was a visionary figure, motivated purely by his interest in scholarly and academic matters. This list of personality words is one the longest in the literature. Examples of the 234 positive traits are Admirable, Brilliant, Charismatic, Dedicated, Eloquent, Forgiving, Gentle, and Honest. Examples of neutral ones are Absentminded, Boyish, Casual, Dreamy, Enigmatic, Frugal, Guileless, and High-spirited. Examples of the negative traits are Argumentative, Brutal, Calculating, Destructive, Egocentric, Foolish, Greedy, and Hostile. Naturally, there are many words for each letter of the alphabet in each of the three categories; these examples are included to give a flavour of the traits in Gunkel’s list. These traits have been used in various projects, notably Image-Chat [[161](#bib.bib161), [162](#bib.bib162)] (see below).

Marilyn Walker at University of California Santa Cruz has played a major role in the development of personality models for natural language processing, and in the development of conversational agents embodying personality. The Film Dialogue Corpus [[179](#bib.bib179)] comprises 862 transcripts of films from the Internet Movie Script Database262626<http://www.imsdb.com/>. Dialogues involve 7,400 different characters, 664,000 lines in total. The dialogues have then been tagged with various kinds of information. First, characters are labelled, based on properties of the films, namely Genre, Director, Year, and on the gender of the character. Second, the lines of each character are grouped together and analysed for various personality-indicating features, including Basic (number of tokens spoken by a character, number of turns), Sentiment Polarity (on a scale of Positive to Negative), Dialogue Act, Passive Sentence Ratio, Linguistic Inquiry Word
Count (LIWC) word categories, and others. The Film Dialogue Corpus contains all this information. It does not specify personality as such; however, the authors show how to use this information to train a model which can infer the personality of each character. Finally, the trained model is used to control parameters of their PERSONAGE generator, which can generate versions of sentences with different personalities.

The CMU Movie Summary Dataset [[12](#bib.bib12)] follows a similar approach and uses information from Wikipedia and Freebase. 42,305 film plot summaries are taken from the Wikipedia. These contain phrases such as ‘rebel leader Princess Leia’. the texts are analysed using CoreNLP272727<http://nlp.stanford.edu/software/corenlp.shtml> in order to extract Agent verbs, Patient verbs and Attributes. The authors argue that these are important in determining personality because they imply the actions carried out by a character, the actions carried out by others on the character, and the qualities or attributes of these actions.

The next step is to use Freebase282828<http://download.freebase.com/datadumps/> which contains detailed information about films and the characters within them. In particular, films are tagged with genre categories such as ‘Epic Western’, and characters are linked to the actors who play them, with biographical information on these actors also being available.

According to the authors, a persona can be linked to three word distributions, concerning agent, patient and attribute.
They use two models (Dirichlet Persona Model and Persona Regression Model) to find clusterings of words to topics (e.g. ‘strangle’ is a type of Assault), topics to personas (e.g. VILLIANS perform many Assaults), and characters to personas (e.g. Darth Vader is a VILLAIN).

TV Tropes292929<http://tvtropes.org> contains common ‘Tropes’ submitted by users in relation to TV, film and fictional works. Tropes are noun phrases which aptly characterise aspects of a narrative or character. The authors extract 72 tropes which can be associated with a character, phrases such as THE CORRUPT CORPORATE EXECUTIVE, or THE HARDBOILED DETECTIVE. These are then manually linked to 501 individual film characters, as identified earlier. This gold-standard data is then used to evaluate the two topic models.

The dataset itself consists of (1) Information for 81,741 films, obtained from Freebase, including name, release date and genre; (2) Information about 450,669 characters in these films, linked to the above, including film, character data and links to Freebase data; (3) 72 different character Tropes, together with 501 film characters, each assigned a Trope; (4) 970 character names in films, linked to 2,666 Trope instances.

Overall, this is an important dataset because it is the first which links Tropes to characters in a way which can be used for training a chatbot with personality. In addition, of course, it is introducing the idea of using Tropes to define personality alongside other approaches (see Tables [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") and [3](#S4.T3 "Table 3 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")).

The Speaker Model Dataset is discussed by Li et al. [[90](#bib.bib90)]. It contains 24,725,711 3-turn sequences from 74,003 users, derived from Twitter. the Speaker-Addressee model contains 69,565 dialogue turns for 13 characters in TV show transcripts. These datasets appear to be private, but are included in the table for comparison. The use of these datasets is described below (Section [4](#S4 "4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")).

Joshi et al. [[76](#bib.bib76)] proposed the The Personalized-Dialog dataset which is based on the well-known bAbI dialogue dataset [[22](#bib.bib22)]. The original dataset uses a knowledge base of restaurants. For each there is a cuisine (10 types, e.g. English), location (10 e.g. Tokyo), a price range (cheap, moderate, expensive), rating (1-8), and party size (2, 4, 6, 8). Each restaurant also has an address and a phone number. The dataset consists of a set of synthetic structured dialogues, based on the knowledge base. The aim is to enquire about restaurants and book a table. Utterances in the dataset are created artificially using patterns, 43 for the user and 20 for the bot.

In their work, Joshi et al. produce a synthetic personalised dataset which is modelled on the original. First, five attributes are added to each restaurant in the KB, cuisine type (vegetarian, non-vegetarian), speciality dish, social media links, parking information, and public transport information. Second, each dialogue starts with a user profile, specifying gender (m/f), age (young, middle-aged, elderly), and favourite food. Thirdly, the linguistic patterns are augmented to take into account profile information; For each of the 15 bot patterns, there are now 6 variants (2 genders \* 3 ages) with different usage for each. For example, for the older ages, a more formal style is adopted. The user patterns remain the same.

As in the original work [[22](#bib.bib22)], the dataset is created algorithmically, but the decisions now make reference to the profile information at the start of each dialogue. For example, when offering restaurants to the user, they are proposed based on their rating, with additional points for matching the user’s diet preference (vegetarian or not) and favourite food. Thus, choice of proposed restaurants is now influenced by user profile. Similarly, depending on the age and gender of the user, the patterns used to create the bot’s utterance are chosen accordingly. In addition, when asked for contact information, the bot returns social media if young, or phone if middle-aged/elderly. In a similar way, when asked for directions, the bot returns address and public transport information if the restaurant is cheap, or address and parking if it is moderately priced/expensive.

The dataset is used to evaluate various models, including rule-based systems, trained embeddings, and end-to-end memory networks.

In general, this work shows how a personalised restaurant dataset can be created algorithmically, as a first step towards producing training data which is tailored to a person’s profile.

Chu et al. [[32](#bib.bib32)] make use of the CMU Movie Summary Dataset [[12](#bib.bib12)] discussed above, as well as creating two new datasets. To build the IMDB Dialogue Snippet Dataset, they extract quotations for selected film characters from the IMDB Quotes website. There are 13,874 quotes for training, and 1,734 each for validation and testing. A quote may contain multiple dialogue turns; naturally, one of the characters in the quote must be the person of interest. Next, they create the Character Trope Description Dataset using information from TVTropes303030<http://tvtropes.org>. Along with each Trope there is a textual description. These two datasets are aligned, so that for a character we can see the quotes, the Trope of the character (e.g. Lovable Rogue) and the Trope description. Note that the aim of the work here is to characterise Personas in a pre-existing dialogue, not to produce a chatbot.

The starting point of the Image-Chat dataset [[161](#bib.bib161)] is 215 style traits which have been selected from a set of 638 traits created by Gunkel313131http://ideonomy.mit.edu/essays/traits.html (see Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). The original 638 traits are already divided into three classes: positive, neutral, and negative, and selections are made from these to make up the set of 215. Traits which are applicable to captioning are chosen, for example sweet, happy (positive), old-fashioned, skeptical (neutral), anxious, childish (negative). Traits considered not applicable to captions are not used (e.g. allocentric, insouciant). The images used come from the YFCC100M Dataset.

The dataset is created using crowdworkers. In order to generate a dialogue, an image is first chosen at random. Two crowdworkers are chosen for the dialogue and each is assigned one style trait at random. They are then asked to create a three-turn dialogue based on the image. The emphasis is on the dialogue being interesting and engaging, and there is no requirement to refer to specific factual aspects of the image.

In a quality control process, a subset of the data was inspected by further crowdworkers, who found that 92.8% of the time the dialogue clearly fitted the image, 83.1% clearly fitted the styles assigned to the crowdworkers, and 80.5% fitted both the image and the styles. So, as with many other datasets created using the crowd, the participants proved in the main to be imaginative and capable.

Persona Chat [[196](#bib.bib196)] consists of a set of 10,907 dialogues created by pairs of Mechanical Turk workers. The starting point is a set of 1,155 persona specifications, which were created in the first phase of the project. A persona here consists of five profile sentences (each 15 words or less) describing a person. Turkers were asked to create such personas at random, by following an persona provided. In the second phase, the collected personas were revised by further Turkers, in order to refine the wording, and hence to avoid later problems of repetition. In the third phase, Turkers were divided randomly into pairs and each person was assigned a random persona from the collected set. They were then asked to engage in dialogue with each other, each person following the ‘personality’ of their assigned persona. Each turn in the dialogue was 15 words maximum, and dialogues consisted of 12-18 turns in total (6-8 for each participant).

In summary, Persona Chat consists of general information-seeking chat. It seems that the Turkers used the personas very skilfully, resulting in some convincing dialogues. The specification of personas as five sentences seemed to have worked well, even though they are created from random combinations of personal characteristics. Naturally a persona in the sense used here is not the same as a personality; the personas are random combinations of personal facts and characteristics. However, this work and its predecessor, Image-Chat (see above) have been extremely influential. The dialogues are remarkably plausible and flow very naturally. These datasets have been widely used to evaluate other models, and other datasets based on the same idea have also been developed (see JPersonaChat below). As a method of specifying personality, this seems to be the dominant method being used today. It is much richer than a traditional specification such as Big-5, it can be used in many types of dialogue model, it can be integrated into the model in different ways (e.g. prefixing the content sentences in the dialogue model by the persona sentences – see Table 3, line 3 – or conditioning on a vector created with the persona sentences). Moreover, five sentences seems to provide enough information while at the same time being practical.

ConvAI2 [[40](#bib.bib40)] was created for the ConvAI2 evaluation campaign. It consists of Persona-Chat plus an additional 100 personas and 1,015 dialogues, used for evaluation.

The Personality Chat Dataset [[119](#bib.bib119)] consists of 100 chat scenarios, each for 5 personalities, in 9 languages. The personalities are Professional, Friendly, Witty, Caring, and Enthusiastic.

Tigunova et al. [[173](#bib.bib173)] present the Movie Character Attributes (MovieChAtt) Dataset. This is based on the Cornell Movie-Dialogs Corpus [[36](#bib.bib36)]. Characters who have 20 lines or more are analysed. The Internet Movie Database(IMDb) was used to look up the gender and age of actors who played characters in the films, and hence to assign these attribute-value pairs to the film characters. Crowdworkers then assigned Professions to the characters. They did this by looking up the characters in Wikipedia articles about the films. In addition, working with the Persona-Chat dataset [[196](#bib.bib196)] (see Table [2](#S2.T2 "Table 2 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")) personas were labelled with Profession, Gender, and Family Status. The result was 1,147 personas with a profession label, 1,316 with gender and 2,302 with family status. Thirdly, the authors used Reddit discussions in the ‘iama’ and ‘askreddit’ subforums, extracted from a public crawl323232<https://files.pushshift.io/reddit/>. Users were labelled with Profession, Gender, Age and Family status using pattern-matching methods. There are about 400 users labelled with each of these four attribute-value pairs. The authors present four Hidden Attribute Model classifiers and evaluate them on their datasets.

The PersonalDialog dataset [[198](#bib.bib198)] consists of a large set of dialogues extracted from logs of Weibo, a well-known Chinese social media site. Weibo itself provides no explicit personality information. Instead, the authors extract this information from the dialogues, using classifiers which they designed and trained. The personality information is then specified as a set of attribute-value pairs. The attributes include age, gender, language, speaking style, level of knowledge, areas of expertise, accent, location, interest. This dataset is large: There are 20.83 million dialogues over 8.47 million users, with 56.25 million utterances in total.

Wang et al. [[181](#bib.bib181)] develop an interesting dataset, Persuasion-ForGood, which includes dialogues where one participant persuades the other to donate to charity (see Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). The underlying personality representation is a vector of 23 dimensions, including Big-5 [[54](#bib.bib54)], Moral Foundations [[59](#bib.bib59)], Schwartz Portrait Value [[33](#bib.bib33)], and Decision-Making Style [[63](#bib.bib63)]. A classifier combining LSTM and Recurrent CNN was developed to recognise persuasion strategy. However, a persuasive chatbot was not developed in the work reported.

Their goals are to link information about a person to the outcome of the persuasion process, and to investigate which persuasion strategies are most effective, given information about a person, including their personality.

This dataset uses multiple personality indicators, drawn from four different personality classification systems, to create the 23-dimension vector referred to above. This is an unusual approach, which we have not seen elsewhere.

IT-ConvAI2 [[100](#bib.bib100)] is based on ConvAI2 (itself based on Persona-Chat). It consists of 1,595 dialogues, selected from ConvAI2, which ask about persona information, with the persona information itself removed from the dialogue. Liu et al. [[100](#bib.bib100)] use this to evaluate their model.

JPersonaChat [[168](#bib.bib168)] is based on Persona-Chat citezhang2018personalizing (see above) and replicates the approach for Japanese. There are 100 personas, specified with 5 sentences each, and 5,000 dialogues.

The PersonageNLG dataset [[140](#bib.bib140)] contains 88,855 restaurant recommendations, which vary by Big-5 personality traits, namely agreeable, disagreeable, conscientious, unconscientious, and extrovert. Note, therefore, that this is text in different styles, it is not a dialogue dataset. The authors argue that Big-5 types can be seen in language at the lexical, syntactic and semantic levels [[108](#bib.bib108)]. The dataset is created automatically by the PERSONAGE program, which is described by Mairesse et al. [[108](#bib.bib108)].

In Personage, there are both lexical and syntactic variations. It uses aggregation operations and pragmatic operations. Aggregation joins texts together, e.g. Extrovert person may use ‘with’, ‘and’, ‘also’. Pragmatic operations include addition of qualifying words such as ‘rather’ before adjectives such as ‘expensive’.

The essence of this work is that it links Big-5 personality types to characteristics of language at the lexical, syntactic and semantic levels. It also describes the PERSONAGE program which is a statistical generator of text in different personalities. This is an unusual approach, as other researchers either specify personalities in advance (e.g. Persona-Chat) and then generate dialogues with those personalities using crowdworkers, or they capture natural dialogues from Blogs, social media sites, films or TV programs, and then retrospectively assign personality specifications to the users/characters.

## 4 Chatbots with Personality

We now summarise some of the recent work, organising the analysis first around the personality model used (Table [3](#S4.T3 "Table 3 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") and, within that, by the method of embodying the personality in the chatbot (Table [4](#S4.T4 "Table 4 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). See also Table [5](#S4.T5 "Table 5 ‣ 4.8 Implicit – Using Dialogues/Monologues ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). Please note that this discussion is therefore not chronological, so that important earlier work using one personality model may be discussed after later work using another personality model.

Table 3: Personality specifications used in chatbot models.

| Pre-existing Personality Schemes | Used By |
| --- | --- |
| Introversion / Extraversion | [[160](#bib.bib160)] |
| Personality Dimensions |  |
| Big-5 / OCEAN | [[11](#bib.bib11)][[109](#bib.bib109)] [[130](#bib.bib130)] [[129](#bib.bib129)] [[203](#bib.bib203)] [[160](#bib.bib160)] [[89](#bib.bib89)] [[16](#bib.bib16)] [[72](#bib.bib72)] [[147](#bib.bib147)] [[205](#bib.bib205)] |
| 16 Personality Factor (16PF) |  |
| Interpersonal Reactivity Index (IRI) | [[89](#bib.bib89)] |
| Chatbot Personality Schemes | Used By |
| Traits | [[161](#bib.bib161)] [[202](#bib.bib202)] |
| Character Tropes | [[12](#bib.bib12)] [[32](#bib.bib32)] |
| Descriptive Sentences | [[21](#bib.bib21)] [[116](#bib.bib116)] [[196](#bib.bib196)] [[40](#bib.bib40)] [[165](#bib.bib165)] [[185](#bib.bib185)] [[92](#bib.bib92)] [[112](#bib.bib112)] [[26](#bib.bib26)] [[48](#bib.bib48)] [[100](#bib.bib100)] [[190](#bib.bib190)] [[168](#bib.bib168)] |
| Attribute-Value Pairs | [[76](#bib.bib76)] [[192](#bib.bib192)] [[137](#bib.bib137)] [[104](#bib.bib104)] [[198](#bib.bib198)] |
| Implicit Personality Schemes | Used By |
| Monologues from TV/Film/Other | [[6](#bib.bib6)] [[90](#bib.bib90)] [[116](#bib.bib116)] |
| Dialogues from TV/Film/Other | [[153](#bib.bib153)] [[156](#bib.bib156)] [[90](#bib.bib90)] [[84](#bib.bib84)] [[124](#bib.bib124)] [[197](#bib.bib197)] [[32](#bib.bib32)] [[106](#bib.bib106)] [[173](#bib.bib173)] [[105](#bib.bib105)] [[136](#bib.bib136)] [[200](#bib.bib200)] |
| Other Related Measures | Used By |
| Templates | [[129](#bib.bib129)] [[130](#bib.bib130)] |
| Genre Text | [[114](#bib.bib114)] [[126](#bib.bib126)] |
| Other Linked Factors | [[178](#bib.bib178)] [[159](#bib.bib159)] |
| Historical Personas | [[65](#bib.bib65)] [[118](#bib.bib118)] [[31](#bib.bib31)] [[182](#bib.bib182)] [[21](#bib.bib21)] |


Table 4: Methods to embody personality in chatbot models. The categories used are broad, and they are not exclusive, so a model can be cited on several lines. The table is indicative only, to show general trends.

| BERT | [[200](#bib.bib200)] |
| --- | --- |
| CNN | [[136](#bib.bib136)] [[200](#bib.bib200)] |
| Condition output on personality vector | [[102](#bib.bib102)] [[192](#bib.bib192)] |
| Generative Adversarial Network | [[48](#bib.bib48)] |
| GPT | [[26](#bib.bib26)] [[100](#bib.bib100)] [[190](#bib.bib190)] [[72](#bib.bib72)] |
| Joint Training (parameter sharing) | [[102](#bib.bib102)] |
| Memory Network (incl. End-to-End) | [[76](#bib.bib76)] [[196](#bib.bib196)] [[104](#bib.bib104)] [[165](#bib.bib165)] [[105](#bib.bib105)] [[48](#bib.bib48)] |
| Prefix with descriptive sentences | [[76](#bib.bib76)] [[161](#bib.bib161)] [[185](#bib.bib185)] [[26](#bib.bib26)] |
| Prompt | [[89](#bib.bib89)] [[72](#bib.bib72)] [[140](#bib.bib140)] [[147](#bib.bib147)] |
| Seq-to-Seq | [[102](#bib.bib102)] [[124](#bib.bib124)] [[192](#bib.bib192)] [[197](#bib.bib197)] [[130](#bib.bib130)][[129](#bib.bib129)] [[196](#bib.bib196)] [[198](#bib.bib198)] [[105](#bib.bib105)] [[205](#bib.bib205)] |
| Symbolic Template | [[65](#bib.bib65)] [[118](#bib.bib118)] [[31](#bib.bib31)] [[129](#bib.bib129)] [[130](#bib.bib130)] [[202](#bib.bib202)] |
| Transformer | [[161](#bib.bib161)] [[106](#bib.bib106)] [[185](#bib.bib185)] [[112](#bib.bib112)] [[105](#bib.bib105)] [[136](#bib.bib136)] [[26](#bib.bib26)] [[100](#bib.bib100)] [[200](#bib.bib200)] |
| Variational AutoEncoder | [[165](#bib.bib165)] |

### 4.1 IntroversionExtraversion

The aim of Shumanov and Lester [[160](#bib.bib160)] is to investigate whether congruent consumer-chatbot personality will benefit the user’s engagement with the chatbot and improve the user’s purchasing behaviour in a commercial setting. The work focuses on Big-5 personality, and specifically Introversion-Extraversion. Personality was manipulated using word-frequency usage data based on the Linguistic Inquiry and Word Count word association method [[171](#bib.bib171)]. Personality recognition was carried out using an ML classifier. 57,000 chatbot dialogues with live users was carried out in an experimental setting. Interestingly, some were transcribed from voice dialogues. The domain was mobile phones, and the dialogues concerned enquiries about recharging credit, account balances and billing. The personality of users (just introversion-extraversion) was determined after the dialogue had taken place, with a classifier [[149](#bib.bib149), [132](#bib.bib132), [8](#bib.bib8)]. The method uses GloVe embeddings, combined for a text, which are input to a Gaussian Processes classifier. The chatbot personality was manipulated in terms of vocabulary usage to be either Introvert or Extravert. When a user contacted the chatbot to make an enquiry, they were assigned at random to either the Introvert version or the Extravert version. Purchasing behaviour was measured by the number of recharge services bought, while Engagement was measured by average duration of interaction with the chatbot Both purchasing and engagement improved when the personalities of the user and the chatbot were the same, according to their findings.

### 4.2 Big-5

Xing and Fernández [[189](#bib.bib189), [188](#bib.bib188)] work with the seq-to-seq personality model of Li et al. [[90](#bib.bib90)]. They use the Big-5 model of personality, pre-train on the OpenSubtitles dataset [[172](#bib.bib172)], and then train on transcripts from the TV shows ‘Friends’ and ‘The Big Bang Theory’. For each character, they estimate the Big-5 personality by applying the recogniser of Mairesse et al. [[110](#bib.bib110)] to a sample of a character’s utterances in the collection. This classifier gives a vector with scores for each Big-5 trait (see Table [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). Now, the evaluation is interesting. Based on the outputs of their seq-to-seq model, they classify a sample of these into Big-5 vectors, again using the Mairesse tool. Finally, they compare these to the Gold-standard vectors; more specifically, they use a Support Vector Machine (SVM) classifier to try to establish the Gold-standard classes from those produced by the model. Results returned are above the baseline, suggesting the potential of this approach.

Wang et al. [[181](#bib.bib181)] develop an interesting dataset, Persuasion-ForGood, which includes dialogues where one participant persuades the other to donate to charity (see Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). The underlying personality representation is a vector of 23 dimensions, including Big-5 [[54](#bib.bib54)], Moral Foundations [[59](#bib.bib59)], Schwartz Portrait Value [[33](#bib.bib33)], and Decision-Making Style [[63](#bib.bib63)]. A classifier combining LSTM and Recurrent CNN was developed to recognise persuasion strategy. However, a persuasive chatbot was not developed in the work reported.

Li et al. [[89](#bib.bib89)] present a method for using prompts in order to identify personality. This was a participant at WASSA@ACL-2022 [[16](#bib.bib16)]. The personality methods are Big-5 and IRI (Table [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). The prompt is a fixed template which is joined to the original input for learning. Data augmentation is used and an ensemble method is adopted, working over 3 pre-trained models.

The extensive work carried out by Marilyn Walker at University of California Santa Cruz has tended to focus on personality specified using Big-5 (see Table [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")).
The work of Oraby et al. [[130](#bib.bib130)] combines symbolic and neural network approaches to personality in an interesting way. The starting point is the PERSONAGE corpus [[129](#bib.bib129)] which contains reports on restaurants expressed in different Big-5 personalities. They then train a seq-to-seq model, not on the texts but on the symbolic dialogue acts and associated parameters (e.g. which personality it is). At the end, a symbolic post-processing phase converts the dialogue act back into a sentence. In essence, when testing, if a combination of personalities is used, the output will combine qualities of those personalities.

Oraby et al. [[129](#bib.bib129)] compare three different seq-to-seq models which specify personality in different ways. The No-supervision model has simple input and output. The Token model encodes the personality as a single token. The Context model encodes the 36 style values, based on 5 aggregation operations and 19 pragmatic markers. In the results, the Context model is the best performing.

In Ramirez et al. [[140](#bib.bib140)], a prompt-based approach is used. The Big-5 types adopted are agreeable, disagreeable, conscientious, unconscientious, and extravert.
There are two types of prompt: (1) Data-to-text – generating text from a representation which includes personality; (2) Textual-style-transfer – converting the meaning representation to textual form. They train a BERT model on 4,000 texts from the PersonageNLG dataset, i.e. 800 per each of the 5 Big-5 personalities.
The Jurassic-1 Jumbo 175B parameter PLM is used for their experiments; this is an autoregressive language model. Training data-to-text gives better results.

In the GERP model, Zhou et al. [[205](#bib.bib205)] aim to produce a response, based on the personality, which is correct in emotion. Personality is based on the Big-5 scheme.

Jiang et al. [[72](#bib.bib72)] work with Large Language Models (LLMs) ChatGPT and GPT-4. They first create personalities based on Big-5 and use them to make the LLMs take the human 44-item personality test including writing a story. The test results produced by the LLMs are assessed for their Big-5 personalities, both using automatic and human methods. The results of the evaluation are consistent with the originally intended personalities.

Safdari et al. [[147](#bib.bib147)] present a method for testing the personality on LLMs. They use the IPIP-NEO [33] version of the Revised NEO Personality Inventory [19] as well as Big-5. Like Jiang et al. [[72](#bib.bib72)] They find that the LLMS can be made to mimic the specified personality under these tests.

### 4.3 Interpersonal Reactivity Index (IRI)

The work of Li et al. [[89](#bib.bib89)] is described above under Big-5. The same method, based on prompts, is used to predict IRI.

### 4.4 Traits

Shuster et al. [[161](#bib.bib161)] first present the Image-Chat dataset (Table [2](#S2.T2 "Table 2 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")) which is described in Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). As we saw, it consists of a set of images, where for each there is a dialogue between two crowdworkers. Each crowdworker is assigned a Gunkel personalty trait [[61](#bib.bib61)]. The generative dialogue model comprises three components, an Image Encoder, a Style Encoder, which transforms a trait into a distributed vector, 500 dimensions for retrieval, 300 for generation, and a Dialogue Encoder, based on Transformers [[174](#bib.bib174)]. The system is pre-trained on a large Reddit dialogue dataset, using the method of Mazare et al. [[116](#bib.bib116)]. The encoded image is added in the form of a token at the end of the Transformer encoder output. The trait encoding is added to the beginning of the dialogue history which is input to the Dialogue Encoder. This is therefore a form of ‘Prefix with descriptive sentences’ in Table [4](#S4.T4 "Table 4 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). Human evaluation is carried out, using images with associated dialogue which are not in the Image-Chat dataset.

The social assistant of Weitz [[182](#bib.bib182)] and Zhou et al. [[202](#bib.bib202)] is outlined in the ‘Other’ subsection (see below). However, the personality of this chatbot is also partly specified in terms of Traits (e.g. Figure 5 on page 63).

### 4.5 Character Tropes

Bamman et al. [[12](#bib.bib12)] first used tropes to characterise personalities in film dialogues (see Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). Chu et al. also built a personality classifier based on tropes. However, neither built a dialogue system as such.

### 4.6 Descriptive Sentences

Zhang et al. [[196](#bib.bib196)] first present the Persona-Chat dataset (see Table [2](#S2.T2 "Table 2 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"), Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). They then discuss several possible models, some using ranking to select and output, others using a Seq-to-Seq model to generate the output. In particular, one model uses Seq-to-seq augmented with a memory network in which the five profile sentences from Persona-chat are individual entries. The models are evaluated by predicting the next utterance, and there is also a human evaluation based on Fluency, Engagingness, Consistency and Persona Detection. On Persona Detection, a model using ranking along with Profile Memory appears to perform the best, followed by the Seq-to-seq with Profile Memory.

Mazaré et al. [[116](#bib.bib116)] build on the ideas of Persona-Chat [[196](#bib.bib196)], which uses 1,155 5-line profiles created by crowdworkers (see Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). The general aim here is to predict responses in a conversation, based on the persona of the speaker. A far bigger set of random personas is created as follows. A Persona is constructed using a REDDIT collection of 1.7 billion comments. All comments from a particular user are grouped together. Next, those between 4 and 20 words, containing ’I’ or ’my’, at least one verb and at least one noun/pronoun/adjective are chosen. A persona is limited to N sentences chosen from the resulting set. The main method for doing this is by using a classifier based on a bag of words, which is trained to select Persona-Chat sentences and to reject random comments. There are therefore 4.6 million personas.

A one-hop memory network is used, where the context sentences are the query, and the persona sentences are the memory. The representation, which is a combination of the context sentence and the persona, is compared to a set of candidate responses, and the one which matches best is chosen as the response. Matching is performed using the dot product. When testing, a Transformer-based model incorporating personas works better than the baselines. In general, this work shows that training with a ‘Descriptive Sentences’ approach (Table [3](#S4.T3 "Table 3 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")) can be taken to extremes, and still give good results when evaluated on the original Persona-Chat data.

The aim of Song et al. [[165](#bib.bib165)] is to create more diverse responses from a CA, while incorporating personality. This work is done using the Persona-Chat dataset with the additional test set from the ConvAI2 evaluation. Personality is thus expressed as five sentences. The model used is based on Conditional
Variational AutoEncoders [Zhao2017] and uses aspects of MemN2N [Sukhbaatar 2015)]to incorporate an external memory for the persona information.

Wolf et al. [[185](#bib.bib185)] describe TransferTransfo, a participant at the Conversational Intelligence Challenge 2 (ConvAI2)333333<http://convai.io/>. The model is based on the Generative Pre-Trained Transformer [[138](#bib.bib138)]. Following pre-training on BooksCorpus [[206](#bib.bib206)], the model is trained using Persona-Chat [[196](#bib.bib196)]. The persona is specified by prefixing the dialogue sentences with the corresponding descriptive sentences from Persona-Chat.

The key to the work of Cao et al. [[26](#bib.bib26)] is to carry out various processes on previous dialogue data in order to simplify and improve its processing. These are (1) Data distillation to make data only contain useful sentences, (2) Data diversification to improve diversity of later responses, (3) Data curriculum [[19](#bib.bib19)], i.e. the use of the simplified data for initial training, followed by the original data. The data used is Persona-Chat, so this approach is based on ‘Descriptive Sentences’ in our terminology. The approach can be used with different base models. Here they present versions using Transformers [[174](#bib.bib174)] and GPT2 [[27](#bib.bib27)]. Human evaluation is relative to Fluency, Coherence with dialogue history, and Persona consistency. With Transformers, results are better than the baselines.

The aim of Firdaus et al. [[48](#bib.bib48)] is to generate responses which match the persona and emotion of the user, working in the ‘Descriptive Sentences’ paradigm. The model consists of a generator network, a memory network in which the persona information is encoded, and three discriminators, Empathetic, Persona, and Semantic. The generator is a hierarchical encoder-decoder using BiGRU. The decoder is a single-direction GRU. The three discriminators use GRU to find the distance between a generated response and the ground-truth, in respect of semantics, persona, and empathy. Experiments are conducted on ConvAI2 (based on Persona-Chat). Human evaluation is on the basis of Fluency, Relevance, Persona Consistency, and Emotion Appropriateness.

The key idea of Liu et al. [[100](#bib.bib100)] is to develop a way to retrieve a persona from a large collection which is consistent with an existing 5-line persona of the Persona-Chat form. In this way, the source material for a retrieval model can be enriched. For example, a query about a family situation cannot readily be answered if the existing persona does not specify this. However, the persona expansion must not accidentally contradict the existing persona. The model contains two parts – (1) The Persona Ranking Model (PRM) ranks personas from the entire ConvAI set using natural language inference to prevent conflicts; (2) PS-Transformer selects the most suitable personas from these. PRM uses an existing pretrained natural language inference module [[51](#bib.bib51)]. PS-Transformer is a Transformer model based on OpenAI GPT [[138](#bib.bib138)]. They propose a special dataset for evaluation: IT-ConvAI2 (see Section [3](#S3 "3 Personality Datasets ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). The model achieves good results on the ConvAI2 and IT-ConvAI2 datasets.

The intent of Xu et al. [[190](#bib.bib190)] is to combine information from the persona (in a ‘Descriptive Sentences’ paradigm) and from the dialogue history, in order to generate good responses. They use a Persona Information Memory Selection Network (PMSN) to do this. PMSN is an MLP, trained on previous dialogue data. GPT-2 is used within the generator. There is a multi-hop attention mechanism for previous dialogue information and for persona information. The model is trained on ConvAI2 data. The model can generate a more personalised response than the baselines, according to their evaluation.

### 4.7 Attribute-Value Pairs

Yang et al. [[192](#bib.bib192)] perform personalisation based on user profiles. A seq-to-seq model is used. They use a form of transfer learning: Train first with a large general training dataset, then train with a smaller personalised dataset. They use Sina Weibo conversation data (with no user information), i.e. 4,435,959 post-response pairs (in 219,905 posts) crawled from Sina Weibo by Shang et al. [[152](#bib.bib152)]. They then crawled Sina Weibo themselves for tweets from users who had profile information, extracting the profiles as well. This led to 51,921 post-response pairs with profile data. The profile consists of User identity, Age (in five age bands), Gender (female, male or None), Education, and Location. This is placed in a one-hot vector and then converted to a distributed representation during training. The output of the seq-to-seq is conditioned on this distributed vector. In human evaluation the proposed personalised model outperformed the baselines.

Qian et al. [[137](#bib.bib137)] present an approach based on an attribute-value approach to personality, which they define as ‘the character that the bot plays or performs during conversational interactions’. A key problem they want to address is inconsistent responses to the same question within a session, a well-known problem with chatbots. For example, in their Table 1: User: ‘Are you a boy or a girl?’, Chatbot: ‘I am a boy.’, User: ‘Are you a girl?’, Chatbot: ‘Yes, I am a girl.’. This problem is addressed using profiles. The model is first trained on Chinese social media data. Next, profile information is created, consisting of key-value pairs for different personalities. When running a dialogue, the required profile is specified. If the chatbot is asked a question relating to one of the keys (e.g. ’how old are you?’), the value from the profile is substituted into the answer returned by the chatbot using the position detector. If the chatbot is asked a question not relating to the keys (e.g. ’how are you?) then the chatbot response is used with no substitution.

Luo et al. [[104](#bib.bib104)] are aiming at personalisation in a goal-oriented setting (specifically, restaurant reservation). They use an End-to-End Memory Network (MEMN2N [Bordes, Boureau, and Weston (2017]. Utterances in the dialogue are added to the memory as the dialogue proceeds. A user Profile is originally in attribute-value form, e.g. Gender: Male, Age: Young etc. In their Profile Model, a distributed version of the original profile is used. They also incorporate dialogue from similar users as a global memory. The Preference Model can learn a users preferences in respect of entities in the knowledge base. Combining these two models gives the best performance.

### 4.8 Implicit – Using Dialogues/Monologues

Abushawar and Atwell [[153](#bib.bib153), [156](#bib.bib156)] is a very early project in which the aim was to train a chatbot on corpus data. They used parts of the British National Corpus (BNC) to train ALICE chatbots in different domains such as Sport, World affairs, travel, media and food. They also used BNC London teenager and "loudmouth" transcripts. In such a way, their chatbots could take on different personalities and adopt different styles of language. The personalities are of course implicit, as there is no underlying personality model such as Big-5 etc.

Li et al. [[90](#bib.bib90)] define a persona as a combination of background facts relating to a user, together with their language behaviour and style of interaction. Moreover, they state that the persona of a chatbot should adapt dynamically, depending on who the chatbot is interacting with. In this work, therefore, there is no explicit personality model (e.g. Big-5 or Character Tropes, say). Instead the personality is implicit, deriving from the collective behaviour of the same speaker over many dialogues.

They have two persona models, a single-speaker Speaker model and a dyadic Speaker-Addressee model. The Speaker model captures how the speaker behaves in general, i.e. their persona. The Speaker-Addressee model captures how the speaker behaves when talking to a particular person. This allows for the possibility that a person speakers differently to different people.

The dialogue model is seq2seq. It is trained by inputting the speaker ID and addressee ID along with the context utterance to get the response utterance. They also use domain adaptation training. First, train on a big conversational dataset with no personalisation. Then, train on a smaller dataset with personalisation.

The Speaker model is a vector representation which forms part of the target LSTM in the seq-to-seq model. The vector is learned during training, and the vector for a particular speaker is shared across all training instances for that speaker. Thus, the vector comes to learn the characteristics of a person, and can then condition the output produced for that person. In the Speaker-Addressee model, the principle is similar, but the vector encodes information about both the Speaker and the Addressee. Now, the vector is shared across all training instances between a particular speaker and a particular addressee.

The Speaker model is based on training using specific-speaker data extracted from Twitter. Speakers were selected who participated in between 60 and 300 3-turn conversations on Twitter within a six-month period. The resulting training set contained 24,725,711 3-turn sliding window sequences (i.e. context-message-response) for 74,003 users, having on average 92.24 turns in the dataset. In addition there are 12,000 3-turn conversations for development, validation and testing, 4,000 each. The Speaker-Addressee model is based on scripts from two American television series, Friends and The Big Bang Theory. Thirteen main characters were chosen from these series and used to collect a dataset of 69,565 turns. Development and test sets contain about 2,000 turns each, the remainder are for training. In this model, account is taken both of the speaker and the person to whom they are speaking, in developing the implicit persona of the speaker. Such a model can account for the persona of a person being different, depending on who they are speaking to.

This was one of the earliest attempts to introduce personas into a chatbot, and the results are somewhat inconclusive. The datasets are not public, but some information is included in Table [2](#S2.T2 "Table 2 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots") for comparison.

The aim of Nguyen et al. [[124](#bib.bib124)] is to build chatbots to imitate characters in TV programmes – Barney from How I Met Your Mother, Sheldon from The Big Bang Theory, and Michael from The Office and Joey from Friends. This is done using seq-to-seq model for each character and training it on different data. Because the text of these TV shows is not long enough (about 50,000 utterance-respose pairs), a very interesting form of transfer learning is used, which incorporate the Cornell Movie-Dialogs Corpus [[36](#bib.bib36)] (about 200,000 pairs).
The training regime is as follows: Phase 1: 10k iterations on the Cornell corpus and all four TV shows; Phase 2: 5k iterations on just TV shows; Phase 3: 2k iterations with just utterances by a chosen TV character. Repeat this separately for each character, to create a different chatbot for each one. According to human evaluation, the personalised chatbots performed well.

Luan et al. [[102](#bib.bib102)] adopt joint training in order to achieve personalisation in a conversation agent. There are two models, a seq-to-seq model and an autoencoder. In this formulation, the autoencoder is also a seq-to-seq model. The first model is learning, in the usual way, to respond in a conversation while the autoencoder is trained to predict the input sequence itself. The two are trained with shared parameters so that both learn together and there is generalisation across the two. The seq-to-seq is trained on triples from Twitter. Single posts on Twitter (not interacting with others) of the top 20 users were considered as non-conversational data and used to train the autoencoder. The application domain was technical support. There were two variants of the task; both performed better than the baseline in responding to technical support requests, according to human evaluators.

Zhang et al. [[197](#bib.bib197)] develop five different personalised seq-to-seq models. This is achieved in two stages (i.e. transfer learning). First, train all five chatbots on 1,000,000 post-response pairs from Chinese online forums. Then, train each chatbot on data specific to one user. To create this, five volunteers made available 2,000 messages from their chat history. These are responses with no posts. Therefore, they searched the main data for the closest response and then used the corresponding post to align with the personalised response. The result is five different chatbots, one per user. These were then evaluated by several methods. One is an interesting form of modified Wizard-of-Oz: First, the researcher and the chatbot both receive a tester’s tweets. Both give a response, and the researcher decides which to return to the sender. Then the researcher asks the sender whether all replies were from the researcher (they don’t know about chatbot). An Imitation Rate is calculated in this way.

The key idea of Madotto et al. [[106](#bib.bib106)] is to use few-shot learning – from a few previous dialogues with a particular user, predict their profile. Then they use this to adapt the CA to converse appropriately with that user. Essentially, they sample a batch of personas from the total set. For these, they partition conversation data for these personas into train and validation sets. Then train on them for some iterations. Then sample another batch of personas, and so on. Note that we never train on the personas themselves, only on the past conversations by these personas. They use Persona-Chat dataset. Each persona description has 8.3 unique dialogues. The dialogue model, they say, is a standard Transformer approach [[174](#bib.bib174)]. Results of their training method are comparable to those using the personas directly, and they claim that their dialogues are more consistent.

Qian et al. [[136](#bib.bib136)] and Ma et al. [[105](#bib.bib105)] (see below) are in the same group and propose similar (but not identical) personalisation models. Qian et al. take a retrieval based approach, which selects the best response from a set of candidates. First, they find the language style of the user from their previous dialogues (social media posts and responses). Second, they match utterances from previous dialogues to the current dialogue, to find those that are related by topic. This influences the choice of response candidates. Finally, two forms of matching are combined to choose a response, matching with the personalised style and matching with the dialogue history. The essence of their architectures is an Attentive Module [[204](#bib.bib204)] with single head attention which is based on Transformers [[174](#bib.bib174)]. It matches a query and key-value pair to an output. Unusually, the model uses CNN to extract matching features relating to a response candidate and historical responses. A multi-hop approach to retrieval is adopted to alleviated problems of ambiguity. In the final step, an MLP is used to combine the results of the two matches (style and previous dialogues). Evaluation is relative to Weibo and Reddit (see also Ma et al. below) and is claimed to be better than baselines.

Ma et al. [[105](#bib.bib105)] assert that an approach based on explicit sentences (e.g. Persona-Chat) is not practical in large contexts. Instead, the follow the approach of implicit personality and learn profile information from previous dialogue data for a user. First, using previous interactions, they find the interests of a user, their interests and their writing style. A Transformer language model is used to construct this general user profile. Next, they build a post encoder for each user, which uses the user profile. This uses an RNN based on BiGRU. Third, a key-value memory network holds previous utterance-response pairs for the user. The network is used to create a dynamic profile which can attend to posts from the history which are relevant to the current dialogue. For decoding, there are two mechanisms. A word can be predicted from the general vocabulary or from the personalised vocabulary. To do this ideas from CopyNet [[60](#bib.bib60)] are used. For experiments, data from Weibo and Reddit is used. For evaluation, they use Bleu-1/2, Rouge-L, Dist-1/2 and human evaluation. With the evaluation by humans, the proposed model is judged superior to baselines on Readability, Informativeness and Personalisation.

Zhong et al. [[200](#bib.bib200)] present a personality model using implicit data extracted from dialogue history. Their Modeling and Selecting user Personality (MSP) model tries to extract the most useful persona information from a user’s dialogue history. There are three key refiners: (1) The user refiner selects other users with similar interests to the current user. (2) The topic refiner searches for related topics in both the current user’s history and those of the related users selected by (1). (3) The token refiner finds the best user profiles at the token level. Then, a generator produces responses, using user profiles and the input query. The user refiner uses a BERT model, then compares candidates with the dot-product. The topic refiner also uses a similar BERT approach, while the token refiner adopts Transformers. A Transformer decoder is used. There is also a sentence-matching component using CNN and RNN, which is used to train the token refiner. Evaluation is on Weibo and Reddit datasets.

Table 5: Personality Research Topics.

| Topic | Discussed By |
| --- | --- |
| Dialogues with personality | [[65](#bib.bib65)] [[153](#bib.bib153)][[156](#bib.bib156)] [[118](#bib.bib118)] [[31](#bib.bib31)] [[182](#bib.bib182)][[21](#bib.bib21)] [[41](#bib.bib41)][[82](#bib.bib82)] [[90](#bib.bib90)] [[195](#bib.bib195)] [[102](#bib.bib102)] [[124](#bib.bib124)] [[157](#bib.bib157)] [[167](#bib.bib167)] [[192](#bib.bib192)] [[197](#bib.bib197)] [[32](#bib.bib32)] [[55](#bib.bib55)] [[79](#bib.bib79)] [[116](#bib.bib116)] [[130](#bib.bib130)] [[129](#bib.bib129)] [[137](#bib.bib137)] [[189](#bib.bib189)] [[188](#bib.bib188)] [[196](#bib.bib196)][[104](#bib.bib104)] [[106](#bib.bib106)] [[165](#bib.bib165)] [[173](#bib.bib173)] [[181](#bib.bib181)] [[185](#bib.bib185)] [[198](#bib.bib198)] [[112](#bib.bib112)] [[202](#bib.bib202)] [[105](#bib.bib105)] [[136](#bib.bib136)] [[160](#bib.bib160)] [[26](#bib.bib26)] [[48](#bib.bib48)] [[89](#bib.bib89)] [[100](#bib.bib100)] [[190](#bib.bib190)] [[200](#bib.bib200)] [[72](#bib.bib72)] [[140](#bib.bib140)] [[147](#bib.bib147)] [[205](#bib.bib205)] |
| Generating text in different styles | [[42](#bib.bib42)] [[178](#bib.bib178)] [[108](#bib.bib108)] [[109](#bib.bib109)] [[167](#bib.bib167)] [[197](#bib.bib197)] [[201](#bib.bib201)] [[55](#bib.bib55)] [[79](#bib.bib79)] [[143](#bib.bib143)] [[126](#bib.bib126)] [[129](#bib.bib129)] [[130](#bib.bib130)] [[43](#bib.bib43)] [[64](#bib.bib64)] [[144](#bib.bib144)] |
| Evaluation of personality | [[109](#bib.bib109)] [[85](#bib.bib85)] [[98](#bib.bib98)] [[82](#bib.bib82)] [[167](#bib.bib167)] [[30](#bib.bib30)] [[79](#bib.bib79)] [[189](#bib.bib189)] [[188](#bib.bib188)] [[168](#bib.bib168)] |
| Personality identification | [[110](#bib.bib110)] [[171](#bib.bib171)] [[193](#bib.bib193)][[179](#bib.bib179)] [[3](#bib.bib3)] [[12](#bib.bib12)] [[83](#bib.bib83)] [[107](#bib.bib107)] [[58](#bib.bib58)] [[80](#bib.bib80)] [[135](#bib.bib135)] [[197](#bib.bib197)] [[32](#bib.bib32)] [[189](#bib.bib189)] [[188](#bib.bib188)] [[78](#bib.bib78)] [[173](#bib.bib173)] [[203](#bib.bib203)] [[177](#bib.bib177)] [[17](#bib.bib17)][[15](#bib.bib15)] [[16](#bib.bib16)] [[140](#bib.bib140)] |
| Coherent personality | [[194](#bib.bib194)] [[195](#bib.bib195)] [[137](#bib.bib137)] [[189](#bib.bib189)] [[188](#bib.bib188)] |
| Personality in image captions | ([[121](#bib.bib121)]) [[161](#bib.bib161)] [[162](#bib.bib162)] [[68](#bib.bib68)] |
| Personality and user trust | [[123](#bib.bib123)] [[4](#bib.bib4)] [[203](#bib.bib203)] |
| Prompt methods | [[144](#bib.bib144)] [[10](#bib.bib10)] [[89](#bib.bib89)] [[99](#bib.bib99)] [[140](#bib.bib140)] |
| Chatbot personality discussions | [[88](#bib.bib88)] [[134](#bib.bib134)] |


Table 6: Related Topics.

| Topic | Discussed By |
| --- | --- |
| Early end-to-end chatbots | [[71](#bib.bib71)] [[145](#bib.bib145)] [[14](#bib.bib14)] [[152](#bib.bib152)] [[166](#bib.bib166)] [[175](#bib.bib175)] |
| Origins of neural question answering | [[7](#bib.bib7)] |
| General evaluation of chatbots | [[180](#bib.bib180)] [[154](#bib.bib154)] [[155](#bib.bib155)] [[85](#bib.bib85)] [[2](#bib.bib2)] [[96](#bib.bib96)] [[101](#bib.bib101)] [[113](#bib.bib113)] [[86](#bib.bib86)] [[164](#bib.bib164)] [[23](#bib.bib23)] [[160](#bib.bib160)] [[168](#bib.bib168)] |
| Challenges and competitions | [[40](#bib.bib40)] [[15](#bib.bib15)] [[16](#bib.bib16)] |
| Conversational search | [[18](#bib.bib18)] [[139](#bib.bib139)] [[75](#bib.bib75)] |
| Search personalisation | [[115](#bib.bib115)] [[20](#bib.bib20)] [[41](#bib.bib41)] |
| Personality chatbot reviews | [[5](#bib.bib5)] [[47](#bib.bib47)] |
| General chatbot reviews | [[207](#bib.bib207)] [[70](#bib.bib70)] [[91](#bib.bib91)] [[195](#bib.bib195)] [[49](#bib.bib49)] [[113](#bib.bib113)] [[159](#bib.bib159)] [[35](#bib.bib35)] [[50](#bib.bib50)] [[69](#bib.bib69)] [[120](#bib.bib120)] [[133](#bib.bib133)] [[131](#bib.bib131)] [[148](#bib.bib148)] [[46](#bib.bib46)] [[146](#bib.bib146)] [[141](#bib.bib141)] [[103](#bib.bib103)] [[163](#bib.bib163)] [[191](#bib.bib191)] [[150](#bib.bib150)] [[187](#bib.bib187)] |
| Other related reviews | [[78](#bib.bib78)] [[177](#bib.bib177)] [[17](#bib.bib17)] [[111](#bib.bib111)] [[99](#bib.bib99)] |
| Emotion and empathy in dialogue | [[25](#bib.bib25)] [[13](#bib.bib13)] [[53](#bib.bib53)] [[62](#bib.bib62)] [[201](#bib.bib201)] [[95](#bib.bib95)] [[126](#bib.bib126)] [[142](#bib.bib142)] [[170](#bib.bib170)] [[66](#bib.bib66)] [[52](#bib.bib52)] [[67](#bib.bib67)] [[94](#bib.bib94)] [[93](#bib.bib93)] [[158](#bib.bib158)] [[122](#bib.bib122)] [[202](#bib.bib202)] |

### 4.9 Other

Several bots have been created in order to impersonate famous historical persons.
Heller et al. [[65](#bib.bib65)] discuss a chatbot developed in order to improve student learning. It is based on traditional pattern recognition using AIML templates. The bot imitates the personality of Sigmund Freud and is coded with various materials about him.

Mehta and Corradini [[118](#bib.bib118)] present a chatbot which can converse about Hans Christian Andersen – his life and the fairy tales he wrote. The bot is embodied in a 3D graphical character which can speak and make gestures. The purpose is to educate in an entertaining way. The implementation uses a dialogue-act detector to process the input, determine the intent (e.g. yes/no question) and respond accordingly. It is influenced by ELIZA [[183](#bib.bib183)] and Alice [[1](#bib.bib1)].

InteliWISE [[31](#bib.bib31)] developed a chatbot based on the composer Frederic Chopin. It could talk about Chopin, his life, adventures, compositions, journeys he made, people he was associated with, and so on. Details are scarce, but we can assume it was based on templates and pattern matching.

Weitz [[182](#bib.bib182)] and Zhou et al. [[202](#bib.bib202)] describe a social assistant which is available through Weibo, the Chinese social media site. It is suggested that it has a distinct personality, can empathise with the user and that it has a sense of humour. The bot is able to respond to the same question on different occasions with a different tone. As of 2014, it had been used for 0.5 billion conversations, up to 200,000 of them being simultaneous. Implementation is based on a dialogue manager.

Bogatu et al. [[21](#bib.bib21)] create an agent which can answer questions about historical figures like Albert Einstein and John Lennon. They use two methods: (1) A knowledge base created via an ontology, and (2) Answer selection. The agent is built using ChatScript. They create rules for it by extracting information from Wikipedia and DBpedia. There are two methods for doing this: First, extracting question-answer pairs from Wikipedia, matching the input with the question and outputting the answer; second, matching the question with Wikipedia text directly, converting the best sentence to first person and outputting it. Essentially, this work is stating Wikipedia facts about famous persons, using the first person. There is no formal model of personality, but it is implicit in the material extracted. It can be viewed as a specification via descriptive sentences, but is obviously quite different from Zhang et al. [[196](#bib.bib196)] where sentences are written by crowdworkers.

## 5 Relevant Reviews

In recent years there have been an increasing number of reviews relevant to chatbots and conversational agents (see Table [6](#S4.T6 "Table 6 ‣ 4.8 Implicit – Using Dialogues/Monologues ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). We summarise them here.

Ait et al. [[5](#bib.bib5)] have just published a review of personality-adaptive chatbots. Ferreira and Barbosa [[47](#bib.bib47)] is a survey concerned with the effects on users of personality in chatbots.

Concerning the closely-related topic of emotion in conversation agents, Zhang et al. [[195](#bib.bib195)] present a review of chatbots with emotion which touches on personality. Poria et al. [[133](#bib.bib133)] present a detailed discussion of relevant work, focusing on the detection of conversational emotion. Also of interest, but further from the topic of this article, Maithri et al [[111](#bib.bib111)] review methods for recognising emotion in EEG, facial information and speech systems.

Junior et al. [[78](#bib.bib78)] is a survey of work which aims to extract personality traits from images, image sequences and video. Vora et al. [[177](#bib.bib177)] reviews work on personality prediction from social media sources.
Yan et al. [[191](#bib.bib191)] is an extensive recent review on dialogue systems which touches on personas etc. on p40-41.
Jin et al [[74](#bib.bib74)] review research on text style transfer (TST), going back to the 1980s. They mention the relevance of TST to the creation of chatbot personas, as outlined by McDonald and Pustejovsky [[117](#bib.bib117)] and Hovy [[42](#bib.bib42)], and refer briefly to relevant work such as Li et al. [[90](#bib.bib90)], Zhang et al. [[196](#bib.bib196)] and Shuster et al [[161](#bib.bib161)] [they reference as 2020 ACL] (see our discussion below).

Concerning general reviews on Conversation Agents, one of the earliest, dealing with the pre-neural era, is Shawar et al. [[154](#bib.bib154)]. Deshpande et al. [[38](#bib.bib38)] and Hussain et al. [[69](#bib.bib69)] are general surveys. Fernandes et al. [[46](#bib.bib46)] is a short survey focusing on practical chatbots in the pre-neural paradigm. Csaki, in his dissertation at Budapest University of Technology and Economics [[35](#bib.bib35)] presents a detailed and clear review of previous work on neural chatbots work as well as explaining the underlying theory. Ni et al. [[125](#bib.bib125)] is a comprehensive and detailed survey of theory and practice in neural network dialogue systems. Rapp et al. [[141](#bib.bib141)] is a general review of how users interact with chatbots. Singh and Beniwal [[163](#bib.bib163)] is another recent review.

Xi et al. [[187](#bib.bib187)] is a review of conversation agents based on LLMs. Finally, Liu et al. [[99](#bib.bib99)] is a survey on prompting methods in general which are used for an increasing number of NLP tasks, including personality detection [[89](#bib.bib89)].

## 6 Conclusions

CAs and personality has become a very active area of research. What can we conclude about what has been done so far, and what will happen next?

Our first observation is that the development of the Image-Chat [[161](#bib.bib161)] and Persona-Chat [[196](#bib.bib196)] datasets has been one of the most influential and remarkable areas of work. Underlying this is the idea of using Descriptive Sentences to define personality (Tables [1](#S2.T1 "Table 1 ‣ 2 Personality, Persona, and Profile ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"), [3](#S4.T3 "Table 3 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots")). The transparency of textual information to express personality has great advantages as well as future potential. On the other hand, implicit approaches based on the analysis of previous dialogues etc. are becoming increasingly sophisticated (e.g. [[105](#bib.bib105)]) and can perform in an unsupervised way on large datasets.

Secondly, there has been huge progress in embodying CAs with personality within a short period of time. Many very ingenious and imaginative schemes have been developed and many remarkable datasets have been created.

Thirdly, we can see some hints concerning NN architectures by glancing at Table [4](#S4.T4 "Table 4 ‣ 4 Chatbots with Personality ‣ A Survey of Personality, Persona, and Profile in Conversational Agents and Chatbots"). Seq-to-Seq and Transformer methods underly almost all work, and various kinds of Memory Network are also increasingly used.

However, many of the actual results are somewhat inconclusive. This is partly linked to the difficulty of assessing – especially automatically – the consistency and effectiveness of the personality. A lot of automatic evaluation falls back on simple comparison with a baseline based on, for example, the gold standard next utterance. Regarding human evaluation, it is expensive, and, as yet, it is not quite clear exactly what we are measuring when it comes to personality.

So, turning to the future, we can predict that many new and remarkable datasets will appear, based on the personality schemes discussed in this review. Both explicit and implicit personality schemes will continue, and it is likely the felicitous ways of combining these will be devised. We can also hope that there will be further progress in evaluation methods. Ever since TREC, evaluation and methods to perform it have driven advances in NLP. In our view, with both datasets and evaluation, progress in the models themselves will naturally follow on.

Finally, it is certain that many papers will continue to appear. No doubt, important and relevant papers have accidentally been omitted from this review, for which we apologise in advance. You are welcome to contact the author with suggestions for papers which should be added, and we will do our best to include these in any future versions of this review.

## Acknowledgments

Many thanks to George Kour for the ArXiv style: https://github.com/kourgeorge/arxiv-style. Thanks to Jon Chamberlain, Yunfei Long, and Ravi Shekhar at Essex for their help and encouragement.

## References

* [1]

  B. AbuShawar and E. Atwell.
  Alice chatbot: Trials and outputs.
  Computación y Sistemas, 19(4):625–632, 2015.
* [2]

  B. AbuShawar and E. Atwell.
  Usefulness, localizability, humanness, and language-benefit:
  additional evaluation criteria for natural language dialogue systems.
  International Journal of Speech Technology, 19:373–383, 2016.
* [3]

  S. Adali and J. Golbeck.
  Predicting personality with social behavior.
  In 2012 IEEE/ACM International Conference on Advances in Social
  Networks Analysis and Mining, pages 302–309. IEEE, 2012.
* [4]

  P. Agrawal, A. Suri, and T. Menon.
  A trustworthy, responsible and interpretable system to handle chit
  chat in conversational bots.
  arXiv preprint arXiv:1811.07600, 2018.
* [5]

  T. Ait Baha, M. El Hajji, Y. Es-Saady, and H. Fadili.
  The power of personalization: A systematic review of
  personality-adaptive chatbots.
  SN Computer Science, 4(5):661, 2023.
* [6]

  R. Al-Rfou, M. Pickett, J. Snaider, Y.-H. Sung, B. Strope, and R. Kurzweil.
  Conversational contextual cues: The case of personalization and
  history for response ranking.
  arXiv preprint arXiv:1606.00372, 2016.
* [7]

  J. Andreas, M. Rohrbach, T. Darrell, and D. Klein.
  Learning to compose neural networks for question answering.
  arXiv preprint arXiv:1601.01705, 2016.
* [8]

  P.-H. Arnoux, A. Xu, N. Boyette, J. Mahmud, R. Akkiraju, and V. Sinha.
  25 tweets to know you: A new model to predict personality with social
  media.
  In Proceedings of the international AAAI conference on web and
  social media, volume 11, pages 472–475, 2017.
* [9]

  J. Austin.
  How to Do Things with Words: The William James Lectures
  Delivered at Harvard University in 1955.
  Clarendon Press, Oxford, 1962.
* [10]

  S. H. Bach, V. Sanh, Z.-X. Yong, A. Webson, C. Raffel, N. V. Nayak, A. Sharma,
  T. Kim, M. S. Bari, T. Fevry, et al.
  Promptsource: An integrated development environment and repository
  for natural language prompts.
  arXiv preprint arXiv:2202.01279, 2022.
* [11]

  G. Ball and J. Breese.
  Emotion and personality in a conversational agent.
  Embodied conversational agents, 189, 2000.
* [12]

  D. Bamman, B. O’Connor, and N. A. Smith.
  Learning latent personas of film characters.
  In Proceedings of the 51st Annual Meeting of the Association for
  Computational Linguistics (Volume 1: Long Papers), pages 352–361, 2013.
* [13]

  R. E. Banchs.
  On the construction of more human-like chatbots: Affect and emotion
  analysis of movie dialogue data.
  In 2017 Asia-Pacific Signal and Information Processing
  Association Annual Summit and Conference (APSIPA ASC), pages 1364–1367.
  IEEE, 2017.
* [14]

  R. E. Banchs and H. Li.
  Iris: a chat-oriented dialogue system based on the vector space
  model.
  In Proceedings of the ACL 2012 System Demonstrations, pages
  37–42, 2012.
* [15]

  J. Barnes, O. De Clercq, V. Barriere, S. Tafreshi, S. Alqahtani, J. Sedoc, and
  A. Balahur.
  Proceedings of the 12th workshop on computational approaches to
  subjectivity, sentiment & social media analysis.
  In Proceedings of the 12th Workshop on Computational Approaches
  to Subjectivity, Sentiment & Social Media Analysis. Association for
  Computational Linguistics, 2022.
* [16]

  V. Barriere, S. Tafreshi, J. Sedoc, and S. Alqahtani.
  Wassa 2022 shared task: Predicting empathy, emotion and personality
  in reaction to news stories.
  In Proceedings of the 12th Workshop on Computational Approaches
  to Subjectivity, Sentiment & Social Media Analysis, pages 214–227, 2022.
* [17]

  E. D. Beck and J. J. Jackson.
  A mega-analysis of personality prediction: Robustness and boundary
  conditions.
  Journal of Personality and Social Psychology, 122(3):523, 2022.
* [18]

  N. J. Belkin, C. Cool, A. Stein, and U. Thiel.
  Cases, scripts, and information-seeking strategies: On the design of
  interactive information retrieval systems.
  Expert systems with applications, 9(3):379–395, 1995.
* [19]

  Y. Bengio, J. Louradour, R. Collobert, and J. Weston.
  Curriculum learning.
  In Proceedings of the 26th annual international conference on
  machine learning, pages 41–48, 2009.
* [20]

  P. N. Bennett, R. W. White, W. Chu, S. T. Dumais, P. Bailey, F. Borisyuk, and
  X. Cui.
  Modeling the impact of short-and long-term behavior on search
  personalization.
  In Proceedings of the 35th international ACM SIGIR conference on
  Research and development in information retrieval, pages 185–194, 2012.
* [21]

  A. Bogatu, D. Rotarescu, T. Rebedea, and S. Ruseti.
  Conversational agent that models a historical personality.
  In RoCHI, pages 81–86, 2015.
* [22]

  A. Bordes, Y.-L. Boureau, and J. Weston.
  Learning end-to-end goal-oriented dialog.
  arXiv preprint arXiv:1605.07683, 2016.
* [23]

  S. Borsci, A. Malizia, M. Schmettow, F. Van Der Velde, G. Tariverdiyeva,
  D. Balaji, and A. Chamberlain.
  The chatbot usability scale: the design and pilot of a usability
  scale for interaction with ai-based conversational agents.
  Personal and Ubiquitous Computing, 26:95–119, 2022.
* [24]

  J. M. Burger.
  Personality. PSY 235 Theories of Personality Series.
  Cengage Learning, Stamford, CT, 2014.
* [25]

  N. Byrnes.
  How the bot-y politic influenced this election.
  Technology Rev, 100(10), 2016.
* [26]

  Y. Cao, W. Bi, M. Fang, S. Shi, and D. Tao.
  A model-agnostic data manipulation method for persona-based dialogue
  generation.
  arXiv preprint arXiv:2204.09867, 2022.
* [27]

  Y. Cao, W. Bi, M. Fang, and D. Tao.
  Pretrained language models for dialogue generation with multiple
  input sources.
  arXiv preprint arXiv:2010.07576, 2020.
* [28]

  H. E. Cattell and A. D. Mead.
  The sixteen personality factor questionnaire (16PF).
  Sage Publications, Inc, 2008.
* [29]

  R. B. Cattell and R. C. Johnson.
  Functional psychological testing: Principles and instruments.
  Brunnen Mazel, New York, 1967.
* [30]

  M. K. Chinnakotla and P. Agrawal.
  Lessons from building a large-scale commercial ir-based chatbot for
  an emerging market.
  In The 41st International ACM SIGIR Conference on Research &
  Development in Information Retrieval, pages 1361–1362, 2018.
* [31]

  V. Chopin.
  Inteliwise virtual chopin conversational agent.
  https://chatbots.org/chatbot/virtual\_chopin1/, 2010.
* [32]

  E. Chu, P. Vijayaraghavan, and D. Roy.
  Learning personas from dialogue with attentive memory networks.
  arXiv preprint arXiv:1810.08717, 2018.
* [33]

  J. Cieciuch and E. Davidov.
  A comparison of the invariance properties of the pvq-40 and the
  pvq-21 to measure human values across german and polish samples.
  In Survey Research Methods, volume 6, pages 37–48, 2012.
* [34]

  K. M. Colby, S. Weber, and F. D. Hilf.
  Artificial paranoia.
  Artificial intelligence, 2(1):1–25, 1971.
* [35]

  R. Csaky.
  Deep learning based chatbot models.
  arXiv preprint arXiv:1908.08835, 2019.
* [36]

  C. Danescu-Niculescu-Mizil and L. Lee.
  Chameleons in imagined conversations: A new approach to understanding
  coordination of linguistic style in dialogs.
  arXiv preprint arXiv:1106.3077, 2011.
* [37]

  M. H. Davis.
  Interpersonal reactivity index.
  Online, 1980.
* [38]

  A. Deshpande, A. Shahane, D. Gadre, M. Deshpande, and P. M. Joshi.
  A survey of various chatbot implementation techniques.
  International Journal of Computer Engineering and Applications,
  11(7), 2017.
* [39]

  S. Diederich, A. B. Brendel, and L. M. Kolbe.
  Towards a taxonomy of platforms for conversational agent design.
  Online, 2019.
* [40]

  E. Dinan, V. Logacheva, V. Malykh, A. Miller, K. Shuster, J. Urbanek, D. Kiela,
  A. Szlam, I. Serban, R. Lowe, et al.
  The second conversational intelligence challenge (convai2).
  arXiv preprint arXiv:1902.00098, 2019.
* [41]

  J. Dodge, A. Gane, X. Zhang, A. Bordes, S. Chopra, A. Miller, A. Szlam, and
  J. Weston.
  Evaluating prerequisite qualities for learning end-to-end dialog
  systems.
  arXiv preprint arXiv:1511.06931, 2015.
* [42]

  H. Eduard.
  Generating natural language under pragmatic constraints.
  Journal of Pragmatics, 11(6):689–719, 1987.
* [43]

  E. Elsholz, J. Chamberlain, and U. Kruschwitz.
  Exploring language style in chatbots to increase perceived product
  value and user engagement.
  In Proceedings of the 2019 Conference on Human Information
  Interaction and Retrieval, pages 301–305, 2019.
* [44]

  H. J. Eysenck.
  The structure of human personality.
  Methuen Press, London, 1953.
* [45]

  H. J. Eysenck.
  A short questionnaire for the measurement of two dimensions of
  personality.
  Journal of Applied Psychology, 42(1):14, 1958.
* [46]

  S. Fernandes, R. Gawas, P. Alvares, M. Femandes, D. Kale, and S. Aswale.
  Survey on various conversational systems.
  In 2020 International Conference on Emerging Trends in
  Information Technology and Engineering (ic-ETITE), pages 1–8. IEEE, 2020.
* [47]

  M. Ferreira and B. Barbosa.
  A review on chatbot personality and its expected effects on users.
  Trends, Applications, and Challenges of Chatbot Technology,
  pages 222–243, 2023.
* [48]

  M. Firdaus, N. Thangavelu, A. Ekbal, and P. Bhattacharyya.
  I enjoy writing and playing, do you: A personalized and emotion
  grounded dialogue agent using generative adversarial network.
  IEEE Transactions on Affective Computing, 2022.
* [49]

  J. Gao and M. Galley.
  Neural approaches to conversational ai - question answering,
  task-oriented dialogues and social chatbots.
  arXiv preprint arXiv:1809.08267v2 [cs.CL], 2018.
* [50]

  J. Gao, M. Galley, and L. Li.
  Neural approaches to conversational AI: Question answering,
  task-oriented dialogues and social chatbots.
  Now Foundations and Trends, 2019.
* [51]

  Y. Gao, N. Colombo, and W. Wang.
  Adapting by pruning: A case study on bert.
  arXiv preprint arXiv:2105.03343, 2021.
* [52]

  D. Ghosal, N. Majumder, S. Poria, N. Chhaya, and A. Gelbukh.
  Dialoguegcn: A graph convolutional neural network for emotion
  recognition in conversation.
  arXiv preprint arXiv:1908.11540, 2019.
* [53]

  S. Ghosh, M. Chollet, E. Laksana, L.-P. Morency, and S. Scherer.
  Affect-lm: A neural language model for customizable affective text
  generation.
  arXiv preprint arXiv:1704.06851, 2017.
* [54]

  L. R. Goldberg.
  The development of markers for the big-five factor structure.
  Psychological assessment, 4(1):26, 1992.
* [55]

  L. Goode.
  How google’s eerie robot phone calls hint at ai’s future. may 8,
  2018.
  http://www.wired.com/story/google-duplex-phone-calls-ai-future/,
  2018.
* [56]

  Google.
  Create a persona - conversation design process - conversation design.
  https://designguidelines.withgoogle.com/conversation/conversation-design-process/create-a-persona.html#create-apersona-how-do-i-create-one,
  2019.
* [57]

  S. D. Gosling, P. J. Rentfrow, and W. B. Swann Jr.
  A very brief measure of the big-five personality domains.
  Journal of Research in personality, 37(6):504–528, 2003.
* [58]

  L. Gou, M. X. Zhou, and H. Yang.
  Knowme and shareme: understanding automatically discovered
  personality traits from social media and user sharing preferences.
  In Proceedings of the SIGCHI conference on human factors in
  computing systems, pages 955–964, 2014.
* [59]

  J. Graham, B. A. Nosek, J. Haidt, R. Iyer, S. Koleva, and P. H. Ditto.
  Mapping the moral domain.
  Journal of personality and social psychology, 101(2):366, 2011.
* [60]

  J. Gu, Z. Lu, H. Li, and V. O. Li.
  Incorporating copying mechanism in sequence-to-sequence learning.
  arXiv preprint arXiv:1603.06393, 2016.
* [61]

  P. Gunkel.
  List of personality traits.
  http://ideonomy.mit.edu/essays/traits.html, 2019.
* [62]

  U. Gupta, A. Chatterjee, R. Srikanth, and P. Agrawal.
  A sentiment-and-semantics-based approach for emotion detection in
  textual conversations. neu-ir: Workshop on neural information retrieval,
  sigir 2017, acm.
  arXiv preprint arXiv:1707.06996, 2017.
* [63]

  K. Hamilton, S.-I. Shih, and S. Mohammed.
  The development and validation of the rational and intuitive decision
  styles scale.
  Journal of personality assessment, 98(5):523–535, 2016.
* [64]

  V. Harrison, L. Reed, S. Oraby, and M. Walker.
  Maximizing stylistic control and semantic accuracy in nlg:
  Personality variation and discourse contrast.
  arXiv preprint arXiv:1907.09527, 2019.
* [65]

  B. Heller, M. Proctor, D. Mah, L. Jewell, and B. Cheung.
  Freudbot: An investigation of chatbot technology in distance
  education.
  In EdMedia+ innovate learning, pages 3913–3918. Association
  for the Advancement of Computing in Education (AACE), 2005.
* [66]

  C. Huang, O. R. Zaiane, A. Trabelsi, and N. Dziri.
  Automatic dialogue generation with expressed emotions.
  In Proceedings of the 2018 Conference of the North American
  Chapter of the Association for Computational Linguistics: Human Language
  Technologies, Volume 2 (Short Papers), pages 49–54, 2018.
* [67]

  Y.-H. Huang, S.-R. Lee, M.-Y. Ma, Y.-H. Chen, Y.-W. Yu, and Y.-S. Chen.
  Emotionx-idea: Emotion bert–an affectional model for conversation.
  arXiv preprint arXiv:1908.06264, 2019.
* [68]

  B. Huber, D. McDuff, C. Brockett, M. Galley, and B. Dolan.
  Emotional dialogue generation using image-grounded language models.
  In Proceedings of the 2018 CHI Conference on Human Factors in
  Computing Systems, pages 1–12, 2018.
* [69]

  S. Hussain, O. Ameri Sianaki, and N. Ababneh.
  A survey on conversational agents/chatbots classification and design
  techniques.
  In Web, Artificial Intelligence and Network Applications:
  Proceedings of the Workshops of the 33rd International Conference on Advanced
  Information Networking and Applications (WAINA-2019) 33, pages 946–956.
  Springer, 2019.
* [70]

  H. Io and C. Lee.
  Chatbots and conversational agents: A bibliometric analysis.
  In 2017 IEEE International Conference on Industrial Engineering
  and Engineering Management (IEEM), pages 215–219. IEEE, 2017.
* [71]

  S. Jafarpour, C. J. Burges, and A. Ritter.
  Filter, rank, and transfer the knowledge: Learning to chat.
  Advances in Ranking, 10:2329–9290, 2010.
* [72]

  H. Jiang, X. Zhang, X. Cao, J. Kabbara, and D. Roy.
  Personallm: Investigating the ability of gpt-3.5 to express
  personality traits and gender differences.
  arXiv preprint arXiv:2305.02547, 2023.
* [73]

  H. Jiang, X. Zhang, and J. D. Choi.
  Automatic text-based personality recognition on monologues and
  multiparty dialogues using attentive networks and contextual embeddings
  (student abstract).
  In Proceedings of the AAAI conference on artificial
  intelligence, volume 34, pages 13821–13822, 2020.
* [74]

  D. Jin, Z. Jin, Z. Hu, O. Vechtomova, and R. Mihalcea.
  Deep learning for text style transfer: A survey.
  Computational Linguistics, 48(1):155–205, 2022.
* [75]

  H. Joho, L. Cavedon, J. Arguello, M. Shokouhi, and F. Radlinski.
  Cair’17: First international workshop on conversational approaches to
  information retrieval at sigir 2017.
  In Acm sigir forum, volume 51, pages 114–121. ACM New York,
  NY, USA, 2018.
* [76]

  C. K. Joshi, F. Mi, and B. Faltings.
  Personalization in goal-oriented dialog.
  arXiv preprint arXiv:1706.07503, 2017.
* [77]

  C. Jung.
  Psychological types.
  Routledge, 1923.
* [78]

  J. C. J. Junior, Y. Güçlütürk, M. Pérez,
  U. Güçlü, C. Andujar, X. Baró, H. J. Escalante, I. Guyon,
  M. A. Van Gerven, R. Van Lier, et al.
  First impressions: A survey on vision-based apparent personality
  trait analysis.
  IEEE Transactions on Affective Computing, 13(1):75–95, 2019.
* [79]

  M. Kang.
  A study of chatbot personality based on the purposes of chatbot.
  The Journal of the Korea Contents Association, 18(5):319–329,
  2018.
* [80]

  M. L. Kern, J. C. Eichstaedt, H. A. Schwartz, L. Dziurzynski, L. H. Ungar,
  D. J. Stillwell, M. Kosinski, S. M. Ramones, and M. E. Seligman.
  The online social self: An open vocabulary approach to personality.
  Assessment, 21(2):158–169, 2014.
* [81]

  H. Kim, D. Y. Koh, G. Lee, J.-M. Park, and Y.-k. Lim.
  Designing personalities of conversational agents.
  In Extended Abstracts of the 2019 CHI Conference on Human
  Factors in Computing Systems, pages 1–6, 2019.
* [82]

  W. Knight.
  Amazon working on making alexa recognize your emotions. june 13,
  2016.
  https://www.technologyreview.com/s/601654/amazon-working-on-making-alexa-recognize-your-emotions/,
  2016.
* [83]

  M. Kosinski, D. Stillwell, and T. Graepel.
  Private traits and attributes are predictable from digital records of
  human behavior.
  Proceedings of the national academy of sciences,
  110(15):5802–5805, 2013.
* [84]

  S. Kottur, X. Wang, and V. Carvalho.
  Exploring personalized neural conversational models.
  In IJCAI, pages 3728–3734, 2017.
* [85]

  K. Kuligowska.
  Commercial chatbot: performance evaluation, usability metrics and
  quality standards of embodied conversational agents.
  Professionals Center for Business Research, 2, 2015.
* [86]

  K. Kvale, O. A. Sell, S. Hodnebrog, and A. Følstad.
  Improving conversations: lessons learnt from manual analysis of
  chatbot dialogues.
  In International workshop on chatbot research and design, pages
  187–200. Springer, 2019.
* [87]

  W. G. Lehnert, M. G. Dyer, P. N. Johnson, C. Yang, and S. Harley.
  Boris—an experiment in in-depth understanding of narratives.
  Artificial intelligence, 20(1):15–62, 1983.
* [88]

  N. Lessio and A. Morris.
  Toward design archetypes for conversational agent personality.
  In 2020 IEEE International Conference on Systems, Man, and
  Cybernetics (SMC), pages 3221–3228. IEEE, 2020.
* [89]

  B. Li, Y. Weng, Q. Song, F. Ma, B. Sun, and S. Li.
  Prompt-based pre-trained model for personality and interpersonal
  reactivity prediction.
  arXiv preprint arXiv:2203.12481, 2022.
* [90]

  J. Li, M. Galley, C. Brockett, G. Spithourakis, J. Gao, and W. B. Dolan.
  A persona-based neural conversation model.
  In Proceedings of the 54th Annual Meeting of the Association for
  Computational Linguistics (Volume 1: Long Papers), pages 994–1003, 2016.
* [91]

  Y. Li.
  Conversational systems: A general review.
  https://medium.com/syncedreview/conversational-systems-a-general-review-d47c9f33d5dd,
  2017.
* [92]

  Z. Lin, Z. Liu, G. I. Winata, S. Cahyawijaya, A. Madotto, Y. Bang, E. Ishii,
  and P. Fung.
  Xpersona: Evaluating multilingual personalized chatbot.
  arXiv preprint arXiv:2003.07568, 2020.
* [93]

  Z. Lin, A. Madotto, J. Shin, P. Xu, and P. Fung.
  Moel: Mixture of empathetic listeners.
  arXiv preprint arXiv:1908.07687, 2019.
* [94]

  Z. Lin, P. Xu, G. I. Winata, F. B. Siddique, Z. Liu, J. Shin, and P. Fung.
  Caire: An empathetic neural chatbot.
  arXiv preprint arXiv:1907.12108, 2019.
* [95]

  B. Liu and S. S. Sundar.
  Should machines express sympathy and empathy? experiments with a
  health advice chatbot.
  Cyberpsychology, Behavior, and Social Networking,
  21(10):625–636, 2018.
* [96]

  C.-W. Liu, R. Lowe, I. V. Serban, M. Noseworthy, L. Charlin, and J. Pineau.
  How not to evaluate your dialogue system: An empirical study of
  unsupervised evaluation metrics for dialogue response generation.
  arXiv preprint arXiv:1603.08023, 2016.
* [97]

  J. Liu, Y. Li, and M. Lin.
  Review of intent detection methods in the human-machine dialogue
  system.
  In Journal of physics: conference series, volume 1267, page
  012059. IOP Publishing, 2019.
* [98]

  K. Liu, J. Tolins, J. E. F. Tree, M. Neff, and M. A. Walker.
  Two techniques for assessing virtual agent personality.
  IEEE Transactions on Affective Computing, 7(1):94–105, 2015.
* [99]

  P. Liu, W. Yuan, J. Fu, Z. Jiang, H. Hayashi, and G. Neubig.
  Pre-train, prompt, and predict: A systematic survey of prompting
  methods in natural language processing.
  ACM Computing Surveys, 55(9):1–35, 2023.
* [100]

  Y. Liu, W. Wei, J. Liu, X. Mao, R. Fang, and D. Chen.
  Improving personality consistency in conversation by persona
  extending.
  In Proceedings of the 31st ACM International Conference on
  Information & Knowledge Management, pages 1350–1359, 2022.
* [101]

  R. Lowe, I. V. Serban, M. Noseworthy, L. Charlin, and J. Pineau.
  On the evaluation of dialogue systems with next utterance
  classification.
  arXiv preprint arXiv:1605.05414, 2016.
* [102]

  Y. Luan, C. Brockett, B. Dolan, J. Gao, and M. Galley.
  Multi-task learning for speaker-role adaptation in neural
  conversation models.
  arXiv preprint arXiv:1710.07388, 2017.
* [103]

  B. Luo, R. Y. Lau, C. Li, and Y.-W. Si.
  A critical review of state-of-the-art chatbot designs and
  applications.
  Wiley Interdisciplinary Reviews: Data Mining and Knowledge
  Discovery, 12(1):e1434, 2022.
* [104]

  L. Luo, W. Huang, Q. Zeng, Z. Nie, and X. Sun.
  Learning personalized end-to-end goal-oriented dialog.
  In Proceedings of the AAAI Conference on Artificial
  Intelligence, volume 33, pages 6794–6801, 2019.
* [105]

  Z. Ma, Z. Dou, Y. Zhu, H. Zhong, and J.-R. Wen.
  One chatbot per person: Creating personalized chatbots based on
  implicit user profiles.
  In Proceedings of the 44th international ACM SIGIR conference on
  research and development in information retrieval, pages 555–564, 2021.
* [106]

  A. Madotto, Z. Lin, C.-S. Wu, and P. Fung.
  Personalizing dialogue agents via meta-learning.
  In Proceedings of the 57th Annual Meeting of the Association for
  Computational Linguistics, pages 5454–5459, 2019.
* [107]

  J. Mahmud, M. X. Zhou, N. Megiddo, J. Nichols, and C. Drews.
  Recommending targeted strangers from whom to solicit information on
  social media.
  In Proceedings of the 2013 international conference on
  Intelligent user interfaces, pages 37–48, 2013.
* [108]

  F. Mairesse and M. A. Walker.
  Towards personality-based user adaptation: psychologically informed
  stylistic language generation.
  User Modeling and User-Adapted Interaction, 20:227–278, 2010.
* [109]

  F. Mairesse and M. A. Walker.
  Controlling user perceptions of linguistic style: Trainable
  generation of personality traits.
  Computational Linguistics, 37(3):455–488, 2011.
* [110]

  F. Mairesse, M. A. Walker, M. R. Mehl, and R. K. Moore.
  Using linguistic cues for the automatic recognition of personality in
  conversation and text.
  Journal of artificial intelligence research, 30:457–500, 2007.
* [111]

  M. Maithri, U. Raghavendra, A. Gudigar, J. Samanth, P. D. Barua, M. Murugappan,
  Y. Chakole, and U. R. Acharya.
  Automated emotion recognition: Current trends and future
  perspectives.
  Computer methods and programs in biomedicine, page 106646,
  2022.
* [112]

  B. P. Majumder, H. Jhamtani, T. Berg-Kirkpatrick, and J. McAuley.
  Like hiking? you probably enjoy nature: Persona-grounded dialog with
  commonsense expansions.
  arXiv preprint arXiv:2010.03205, 2020.
* [113]

  J. Masche and N.-T. Le.
  A review of technologies for conversational systems.
  In Advanced Computational Methods for Knowledge Engineering:
  Proceedings of the 5th International Conference on Computer Science, Applied
  Mathematics and Applications, ICCSAMA 2017 5, pages 212–225. Springer,
  2018.
* [114]

  A. Mathews, L. Xie, and X. He.
  Semstyle: Learning to generate stylised image captions using
  unaligned text.
  In Proceedings of the IEEE conference on computer vision and
  pattern recognition, pages 8591–8600, 2018.
* [115]

  N. Matthijs and F. Radlinski.
  Personalizing web search using long term browsing history.
  In Proceedings of the fourth ACM international conference on Web
  search and data mining, pages 25–34, 2011.
* [116]

  P.-E. Mazaré, S. Humeau, M. Raison, and A. Bordes.
  Training millions of personalized dialogue agents.
  arXiv preprint arXiv:1809.01984, 2018.
* [117]

  D. D. McDonald and J. Pustejovsky.
  A computational theory of prose style for natural language
  generation.
  In Second Conference of the European Chapter of the Association
  for Computational Linguistics, 1985.
* [118]

  M. Mehta and A. Corradini.
  Developing a conversational agent using ontologies.
  In Human-Computer Interaction. HCI Intelligent Multimodal
  Interaction Environments: 12th International Conference, HCI International
  2007, Beijing, China, July 22-27, 2007, Proceedings, Part III 12, pages
  154–164. Springer, 2007.
* [119]

  Microsoft.
  Personality chat.
  https://github.com/microsoft/botframework-cli/blob/main/packages/qnamaker/docs/chit-chat-dataset.md,
  2019.
* [120]

  M. Mnasri.
  Recent advances in conversational nlp: Towards the standardization of
  chatbot building.
  arXiv preprint arXiv:1903.09025, 2019.
* [121]

  N. Mostafazadeh, C. Brockett, B. Dolan, M. Galley, J. Gao, G. P. Spithourakis,
  and L. Vanderwende.
  Image-grounded conversations: Multimodal context for natural question
  and response generation.
  arXiv preprint arXiv:1701.08251, 2017.
* [122]

  T. Naous, C. Hokayem, and H. Hajj.
  Empathy-driven arabic conversational chatbot.
  In Proceedings of the Fifth Arabic Natural Language Processing
  Workshop, pages 58–68, 2020.
* [123]

  G. Neff.
  Talking to bots: Symbiotic agency and the case of tay.
  International Journal of Communication, 2016.
* [124]

  H. Nguyen, D. Morales, and T. Chin.
  A neural chatbot with personality.
  URL: https://web. stanford. edu/class/archive/cs/cs224n/cs224n,
  1(174):65, 2017.
* [125]

  J. Ni, T. Young, V. Pandelea, F. Xue, and E. Cambria.
  Recent advances in deep learning based dialogue systems: A systematic
  survey.
  Artificial intelligence review, 56(4):3055–3155, 2023.
* [126]

  T. Niu and M. Bansal.
  Polite dialogue generation without parallel data.
  Transactions of the Association for Computational Linguistics,
  6:373–389, 2018.
* [127]

  W. T. Norman.
  Toward an adequate taxonomy of personality attributes: Replicated
  factor structure in peer nomination personality ratings.
  The journal of abnormal and social psychology, 66(6):574, 1963.
* [128]

  W. T. Norman and L. R. Goldberg.
  Raters, ratees, and randomness in personality structure.
  Journal of Personality and Social Psychology, 4(6):681, 1966.
* [129]

  S. Oraby, L. Reed, S. Tandon, T. Sharath, S. Lukin, and M. Walker.
  Controlling personality-based stylistic variation with neural natural
  language generators.
  arXiv preprint arXiv:1805.08352, 2018.
* [130]

  S. Oraby, L. Reed, S. TS, S. Tandon, and M. Walker.
  Neural multivoice models for expressing novel personalities in
  dialog.
  arXiv preprint arXiv:1809.01331, 2018.
* [131]

  E. W. Pamungkas.
  Emotionally-aware chatbots: A survey.
  arXiv preprint arXiv:1906.09774, 2019.
* [132]

  B. Plank and D. Hovy.
  Personality traits on twitter—or—how to get 1,500 personality
  tests in a week.
  In Proceedings of the 6th workshop on computational approaches
  to subjectivity, sentiment and social media analysis, pages 92–98, 2015.
* [133]

  S. Poria, N. Majumder, R. Mihalcea, and E. Hovy.
  Emotion recognition in conversation: Research challenges, datasets,
  and recent advances.
  IEEE Access, 7:100943–100953, 2019.
* [134]

  A. Pradhan and A. Lazar.
  Hey google, do you have a personality? designing personality and
  personas for conversational agents.
  In Proceedings of the 3rd Conference on Conversational User
  Interfaces, pages 1–4, 2021.
* [135]

  D. Preotiuc-Pietro, J. Carpenter, S. Giorgi, and L. Ungar.
  Studying the dark triad of personality through twitter behavior.
  In Proceedings of the 25th ACM international on conference on
  information and knowledge management, pages 761–770, 2016.
* [136]

  H. Qian, Z. Dou, Y. Zhu, Y. Ma, and J.-R. Wen.
  Learning implicit user profile for personalized retrieval-based
  chatbot.
  In proceedings of the 30th ACM international conference on
  Information & Knowledge Management, pages 1467–1477, 2021.
* [137]

  Q. Qian, M. Huang, H. Zhao, J. Xu, and X. Zhu.
  Assigning personality/profile to a chatting machine for coherent
  conversation generation.
  In Ijcai, pages 4279–4285, 2018.
* [138]

  A. Radford, K. Narasimhan, T. Salimans, I. Sutskever, et al.
  Improving language understanding by generative pre-training.
  Online, 2018.
* [139]

  F. Radlinski and N. Craswell.
  A theoretical framework for conversational search.
  In Proceedings of the 2017 conference on conference human
  information interaction and retrieval, pages 117–126, 2017.
* [140]

  A. Ramirez, M. Alsalihy, K. Aggarwal, C. Li, L. Wu, and M. Walker.
  Controlling personality style in dialogue with zero-shot prompt-based
  learning.
  arXiv preprint arXiv:2302.03848, 2023.
* [141]

  A. Rapp, L. Curti, and A. Boldi.
  The human side of human-chatbot interaction: A systematic literature
  review of ten years of research on text-based chatbots.
  International Journal of Human-Computer Studies, 151:102630,
  2021.
* [142]

  H. Rashkin, E. M. Smith, M. Li, and Y.-L. Boureau.
  Towards empathetic open-domain conversation models: A new benchmark
  and dataset.
  arXiv preprint arXiv:1811.00207, 2018.
* [143]

  L. Reed, S. Oraby, and M. Walker.
  Can neural generators for dialogue learn sentence planning and
  discourse structuring?
  arXiv preprint arXiv:1809.03015, 2018.
* [144]

  E. Reif, D. Ippolito, A. Yuan, A. Coenen, C. Callison-Burch, and J. Wei.
  A recipe for arbitrary text style transfer with large language
  models.
  arXiv preprint arXiv:2109.03910, 2021.
* [145]

  A. Ritter, C. Cherry, and B. Dolan.
  Data-driven response generation in social media.
  In Empirical Methods in Natural Language Processing (EMNLP),
  2011.
* [146]

  S. Roller, E. Dinan, N. Goyal, D. Ju, M. Williamson, Y. Liu, J. Xu, M. Ott,
  K. Shuster, E. M. Smith, et al.
  Recipes for building an open-domain chatbot.
  arXiv preprint arXiv:2004.13637, 2020.
* [147]

  M. Safdari, G. Serapio-García, C. Crepy, S. Fitz, P. Romero, L. Sun,
  M. Abdulhai, A. Faust, and M. Matarić.
  Personality traits in large language models.
  arXiv preprint arXiv:2307.00184, 2023.
* [148]

  S. Santhanam and S. Shaikh.
  A survey of natural language generation techniques with a focus on
  dialogue systems-past, present and future directions.
  arXiv preprint arXiv:1906.00500, 2019.
* [149]

  H. A. Schwartz, J. C. Eichstaedt, M. L. Kern, L. Dziurzynski, S. M. Ramones,
  M. Agrawal, A. Shah, M. Kosinski, D. Stillwell, M. E. Seligman, et al.
  Personality, gender, and age in the language of social media: The
  open-vocabulary approach.
  PloS one, 8(9):e73791, 2013.
* [150]

  V. Scotti, L. Sbattella, and R. Tedesco.
  A primer on seq2seq models for generative chatbots.
  ACM Computing Surveys, 2023.
* [151]

  J. R. Searle.
  Speech acts: An essay in the philosophy of language, volume
  626.
  Cambridge university press, 1969.
* [152]

  L. Shang, Z. Lu, and H. Li.
  Neural responding machine for short-text conversation.
  arXiv preprint arXiv:1503.02364, 2015.
* [153]

  A. Shawar and E. Atwell.
  A chatbot system as a tool to animate a corpus.
  ICAME Journal: International Computer Archive of Modern and
  Medieval English Journal, 29:5–24, 2005.
* [154]

  B. A. Shawar and E. Atwell.
  Chatbots: are they really useful?
  Journal for Language Technology and Computational Linguistics,
  22(1):29–49, 2007.
* [155]

  B. A. Shawar and E. Atwell.
  Different measurement metrics to evaluate a chatbot system.
  In Proceedings of the workshop on bridging the gap: Academic and
  industrial research in dialog technologies, pages 89–96, 2007.
* [156]

  B. A. Shawar and E. S. Atwell.
  Using corpora in machine-learning chatbot systems.
  International journal of corpus linguistics, 10(4):489–516,
  2005.
* [157]

  A. Shevat.
  Designing bots: Creating conversational experiences.
  " O’Reilly Media, Inc.", 2017.
* [158]

  J. Shin, P. Xu, A. Madotto, and P. Fung.
  Generating empathetic responses by looking ahead the user’s
  sentiment.
  arXiv preprint arXiv:1906.08487, 2019.
* [159]

  H.-Y. Shum, X. He, and D. Li.
  From eliza to xiaoice: Challenges and opportunities with social
  chatbots.
  arXiv preprint arXiv:1801.01957, 2018.
* [160]

  M. Shumanov and L. Johnson.
  Making conversations with chatbots more personalized.
  Computers in Human Behavior, 117:106627, 2021.
* [161]

  K. Shuster, S. Humeau, A. Bordes, and J. Weston.
  Image chat: Engaging grounded conversations.
  arXiv preprint arXiv:1811.00945, 2018.
* [162]

  K. Shuster, S. Humeau, H. Hu, A. Bordes, and J. Weston.
  Engaging image captioning via personality.
  arXiv preprint arXiv:1810.10665, 2018.
* [163]

  S. Singh and H. Beniwal.
  A survey on near-human conversational agents.
  Journal of King Saud University-Computer and Information
  Sciences, 34(10):8852–8866, 2022.
* [164]

  K. Sinha, P. Parthasarathi, J. Wang, R. Lowe, W. L. Hamilton, and J. Pineau.
  Learning an unreferenced metric for online dialogue evaluation.
  arXiv preprint arXiv:2005.00583, 2020.
* [165]

  H. Song, W.-N. Zhang, Y. Cui, D. Wang, and T. Liu.
  Exploiting persona information for diverse generation of
  conversational responses.
  arXiv preprint arXiv:1905.12188, 2019.
* [166]

  A. Sordoni, M. Galley, M. Auli, C. Brockett, Y. Ji, M. Mitchell, J.-Y. Nie,
  J. Gao, and B. Dolan.
  A neural network approach to context-sensitive generation of
  conversational responses.
  arXiv preprint arXiv:1506.06714, 2015.
* [167]

  L. Stinson.
  The surprising repercussions of making ai assistants sound human.
  Wired, 2017.
* [168]

  H. Sugiyama, M. Mizukami, T. Arimoto, H. Narimatsu, Y. Chiba, H. Nakajima, and
  T. Meguro.
  Empirical analysis of training strategies of transformer-based
  japanese chit-chat systems.
  In 2022 IEEE Spoken Language Technology Workshop (SLT), pages
  685–691. IEEE, 2023.
* [169]

  I. Sutskever, O. Vinyals, and Q. V. Le.
  Sequence to sequence learning with neural networks.
  Advances in neural information processing systems, 27, 2014.
* [170]

  M. Swayne.
  We want chatbots to express emotions the right way.
  https://www.futurity.org/chatbots-emotions-1902312-2/, 2018.
* [171]

  Y. R. Tausczik and J. W. Pennebaker.
  The psychological meaning of words: Liwc and computerized text
  analysis methods.
  Journal of language and social psychology, 29(1):24–54, 2010.
* [172]

  J. Tiedemann.
  News from opus-a collection of multilingual parallel corpora with
  tools and interfaces.
  In Recent advances in natural language processing, volume 5,
  pages 237–248, 2009.
* [173]

  A. Tigunova, A. Yates, P. Mirza, and G. Weikum.
  Listening between the lines: Learning personal attributes from
  conversations.
  In The World Wide Web Conference, pages 1818–1828, 2019.
* [174]

  A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez,
  Ł. Kaiser, and I. Polosukhin.
  Attention is all you need.
  Advances in neural information processing systems, 30, 2017.
* [175]

  O. Vinyals and Q. Le.
  A neural conversational model.
  arXiv preprint arXiv:1506.05869, 2015.
* [176]

  E. M. Voorhees et al.
  The trec-8 question answering track report.
  In Trec, volume 99, pages 77–82, 1999.
* [177]

  H. Vora, M. Bhamare, and D. K. A. Kumar.
  Personality prediction from social media text: An overview.
  Int. J. Eng. Res, 9(05):352–357, 2020.
* [178]

  M. A. Walker, J. E. Cahn, and S. J. Whittaker.
  Improvising linguistic style: Social and affective bases for agent
  personality.
  In Proceedings of the first international conference on
  Autonomous agents, pages 96–105, 1997.
* [179]

  M. A. Walker, G. I. Lin, J. Sawyer, et al.
  An annotated corpus of film dialogue for learning and characterizing
  character style.
  In LREC, pages 1373–1378, 2012.
* [180]

  M. A. Walker, D. J. Litman, C. A. Kamm, and A. Abella.
  Paradise: A framework for evaluating spoken dialogue agents.
  arXiv preprint cmp-lg/9704004, 1997.
* [181]

  X. Wang, W. Shi, R. Kim, Y. Oh, S. Yang, J. Zhang, and Z. Yu.
  Persuasion for good: Towards a personalized persuasive dialogue
  system for social good.
  arXiv preprint arXiv:1906.06725, 2019.
* [182]

  S. Weitz.
  Meet xiaoice, cortana’s little sister.
  In Microsoft. Online, 2014.
* [183]

  J. Weizenbaum.
  Eliza—a computer program for the study of natural language
  communication between man and machine.
  Communications of the ACM, 9(1):36–45, 1966.
* [184]

  T. Winograd.
  Understanding natural language.
  Cognitive psychology, 3(1):1–191, 1972.
* [185]

  T. Wolf, V. Sanh, J. Chaumond, and C. Delangue.
  Transfertransfo: A transfer learning approach for neural network
  based conversational agents.
  arXiv preprint arXiv:1901.08149, 2019.
* [186]

  W. A. Woods.
  Progress in natural language understanding: an application to lunar
  geology.
  In Proceedings of the June 4-8, 1973, national computer
  conference and exposition, pages 441–450, 1973.
* [187]

  Z. Xi, W. Chen, X. Guo, W. He, Y. Ding, B. Hong, M. Zhang, J. Wang, S. Jin,
  E. Zhou, et al.
  The rise and potential of large language model based agents: A
  survey.
  arXiv preprint arXiv:2309.07864, 2023.
* [188]

  Y. Xing.
  Examining personality differences in chit-chat sequence to sequence
  conversational agents, m.sc. thesis.
  Online, 2018.
* [189]

  Y. Xing and R. Fernández.
  Automatic evaluation of neural personality-based chatbots.
  arXiv preprint arXiv:1810.00472, 2018.
* [190]

  F. Xu, G. Xu, Y. Wang, R. Wang, Q. Ding, P. Liu, and Z. Zhu.
  Diverse dialogue generation by fusing mutual persona-aware and
  self-transferrer.
  Applied Intelligence, pages 1–14, 2022.
* [191]

  R. Yan, J. Li, Z. Yu, et al.
  Deep learning for dialogue systems: Chit-chat and beyond.
  Foundations and Trends® in Information
  Retrieval, 15(5):417–589, 2022.
* [192]

  M. Yang, Z. Zhao, W. Zhao, X. Chen, J. Zhu, L. Zhou, and Z. Cao.
  Personalized response generation via domain adaptation.
  In Proceedings of the 40th International ACM SIGIR Conference on
  Research and Development in Information Retrieval, pages 1021–1024, 2017.
* [193]

  T. Yarkoni.
  Personality in 100,000 words: A large-scale analysis of personality
  and word use among bloggers.
  Journal of research in personality, 44(3):363–373, 2010.
* [194]

  Z. Yu, Z. Xu, A. W. Black, and A. Rudnicky.
  Strategy and policy learning for non-task-oriented conversational
  systems.
  In Proceedings of the 17th annual meeting of the special
  interest group on discourse and dialogue, pages 404–412, 2016.
* [195]

  J. Zhang, N. M. Thalmann, and J. Zheng.
  Combining memory and emotion with dialog on social companion: A
  review.
  In Proceedings of the 29th international conference on computer
  animation and social agents, pages 1–9, 2016.
* [196]

  S. Zhang, E. Dinan, J. Urbanek, A. Szlam, D. Kiela, and J. Weston.
  Personalizing dialogue agents: I have a dog, do you have pets too?
  arXiv preprint arXiv:1801.07243, 2018.
* [197]

  W. Zhang, T. Liu, Y. Wang, and Q. Zhu.
  Neural personalized response generation as domain adaptation.
  arXiv preprint arXiv:1701.02073, 2017.
* [198]

  Y. Zheng, G. Chen, M. Huang, S. Liu, and X. Zhu.
  Personalized dialogue generation with diversified traits.
  arXiv preprint arXiv:1901.09672, 2019.
* [199]

  W. Zhiyuan, C. Jiannong, Y. Ruosong, L. Shuaiqi, and S. Jiaxing.
  Automatically select emotion for response via personality-affected
  emotion transition.
  arXiv preprint arXiv:2106.15846, 2021.
* [200]

  H. Zhong, Z. Dou, Y. Zhu, H. Qian, and J.-R. Wen.
  Less is more: Learning to refine dialogue history for personalized
  dialogue generation.
  arXiv preprint arXiv:2204.08128, 2022.
* [201]

  H. Zhou, M. Huang, T. Zhang, X. Zhu, and B. Liu.
  Emotional chatting machine: Emotional conversation generation with
  internal and external memory.
  arXiv preprint arXiv:1704.01074, 2017.
* [202]

  L. Zhou, J. Gao, D. Li, and H.-Y. Shum.
  The design and implementation of xiaoice, an empathetic social
  chatbot.
  Computational Linguistics, 46(1):53–93, 2020.
* [203]

  M. X. Zhou, G. Mark, J. Li, and H. Yang.
  Trusting virtual agents: The effect of personality.
  ACM Transactions on Interactive Intelligent Systems (TiiS),
  9(2-3):1–36, 2019.
* [204]

  X. Zhou, L. Li, D. Dong, Y. Liu, Y. Chen, W. X. Zhao, D. Yu, and H. Wu.
  Multi-turn response selection for chatbots with deep attention
  matching network.
  In Proceedings of the 56th Annual Meeting of the Association for
  Computational Linguistics (Volume 1: Long Papers), pages 1118–1127, 2018.
* [205]

  Z. Zhou, Y. Shen, X. Chen, and D. Wang.
  Gerp: A personality-based emotional response generation model.
  Applied Sciences, 13(8):5109, 2023.
* [206]

  Y. Zhu, R. Kiros, R. Zemel, R. Salakhutdinov, R. Urtasun, A. Torralba, and
  S. Fidler.
  Aligning books and movies: Towards story-like visual explanations by
  watching movies and reading books.
  In Proceedings of the IEEE international conference on computer
  vision, pages 19–27, 2015.
* [207]

  V. W. Zue and J. R. Glass.
  Conversational interfaces: Advances and challenges.
  Proceedings of the IEEE, 88(8):1166–1180, 2000.